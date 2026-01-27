#!/usr/bin/env python3
"""
MCP Server for SIPUD Inventory System
Provides real-time access to inventory data via Model Context Protocol
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

# Add parent directory to path to import app models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp import types
from mongoengine import connect, disconnect
from dotenv import load_dotenv

# Import SIPUD models
from app.models import (
    Tenant, Product, Lot, InboundOrder, Sale, SaleItem,
    Wastage, ProductBundle, ActivityLog
)

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_HOST = os.environ.get('MONGODB_HOST', 'localhost')
MONGODB_PORT = int(os.environ.get('MONGODB_PORT', '27017'))
MONGODB_DB = os.environ.get('MONGODB_DB', 'inventory_db')

# Default tenant (can be overridden via tool arguments)
DEFAULT_TENANT_SLUG = os.environ.get('MCP_DEFAULT_TENANT', 'puerto-distribucion')

# Initialize MCP server
server = Server("sipud-inventory")


def get_tenant(tenant_slug: Optional[str] = None) -> Tenant:
    """Get tenant by slug or return default tenant"""
    slug = tenant_slug or DEFAULT_TENANT_SLUG
    tenant = Tenant.objects(slug=slug).first()
    if not tenant:
        raise ValueError(f"Tenant '{slug}' not found")
    return tenant


def serialize_product(product: Product) -> dict:
    """Serialize Product to dict with stock information"""
    return {
        "id": str(product.id),
        "name": product.name,
        "sku": product.sku,
        "category": product.category,
        "description": product.description or "",
        "base_price": float(product.base_price) if product.base_price else 0.0,
        "critical_stock": product.critical_stock,
        "total_stock": product.total_stock,  # Computed property
        "is_bundle": product.is_bundle,  # Computed property
        "expiry_date": product.expiry_date.isoformat() if product.expiry_date else None,
        "tenant": product.tenant.slug if product.tenant else None,
    }


def serialize_lot(lot: Lot) -> dict:
    """Serialize Lot to dict"""
    return {
        "id": str(lot.id),
        "lot_code": lot.lot_code,
        "product_name": lot.product.name if lot.product else None,
        "product_id": str(lot.product.id) if lot.product else None,
        "quantity_initial": lot.quantity_initial,
        "quantity_current": lot.quantity_current,
        "expiry_date": lot.expiry_date.isoformat() if lot.expiry_date else None,
        "created_at": lot.created_at.isoformat() if lot.created_at else None,
        "order_id": str(lot.order.id) if lot.order else None,
    }


def serialize_sale(sale: Sale) -> dict:
    """Serialize Sale to dict with items"""
    items = []
    for item in sale.items:
        items.append({
            "product_name": item.product.name if item.product else None,
            "product_id": str(item.product.id) if item.product else None,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price) if item.unit_price else 0.0,
            "subtotal": float(item.subtotal) if item.subtotal else 0.0,
        })

    return {
        "id": str(sale.id),
        "customer_name": sale.customer_name or "",
        "address": sale.address or "",
        "phone": sale.phone or "",
        "status": sale.status,
        "delivery_status": sale.delivery_status or "",
        "payment_method": sale.payment_method or "",
        "payment_confirmed": sale.payment_confirmed,
        "date_created": sale.date_created.isoformat() if sale.date_created else None,
        "items": items,
    }


def serialize_inbound_order(order: InboundOrder) -> dict:
    """Serialize InboundOrder to dict"""
    return {
        "id": str(order.id),
        "supplier_name": order.supplier_name or "",
        "invoice_number": order.invoice_number or "",
        "status": order.status,
        "total": float(order.total) if order.total else 0.0,
        "notes": order.notes or "",
        "date_received": order.date_received.isoformat() if order.date_received else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


def serialize_wastage(wastage: Wastage) -> dict:
    """Serialize Wastage to dict"""
    return {
        "id": str(wastage.id),
        "product_name": wastage.product.name if wastage.product else None,
        "product_id": str(wastage.product.id) if wastage.product else None,
        "quantity": wastage.quantity,
        "reason": wastage.reason,
        "notes": wastage.notes or "",
        "date_created": wastage.date_created.isoformat() if wastage.date_created else None,
    }


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for querying SIPUD inventory"""
    return [
        types.Tool(
            name="get_products",
            description="Get all products with their current stock levels. Optionally filter by category, low stock, or search by name/SKU.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant": {
                        "type": "string",
                        "description": f"Tenant slug (default: {DEFAULT_TENANT_SLUG})",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category",
                    },
                    "low_stock_only": {
                        "type": "boolean",
                        "description": "Only show products below critical stock level",
                    },
                    "search": {
                        "type": "string",
                        "description": "Search by product name or SKU",
                    },
                },
            },
        ),
        types.Tool(
            name="get_product_detail",
            description="Get detailed information about a specific product including stock, lots, and bundle components if applicable.",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID (MongoDB ObjectId)",
                    },
                    "tenant": {
                        "type": "string",
                        "description": f"Tenant slug (default: {DEFAULT_TENANT_SLUG})",
                    },
                },
                "required": ["product_id"],
            },
        ),
        types.Tool(
            name="get_lots",
            description="Get all inventory lots (FIFO batches) with current quantities. Optionally filter by product or show only available lots.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant": {
                        "type": "string",
                        "description": f"Tenant slug (default: {DEFAULT_TENANT_SLUG})",
                    },
                    "product_id": {
                        "type": "string",
                        "description": "Filter by product ID",
                    },
                    "available_only": {
                        "type": "boolean",
                        "description": "Only show lots with quantity_current > 0",
                    },
                },
            },
        ),
        types.Tool(
            name="get_expiring_products",
            description="Get products with lots that are expiring soon (within specified days).",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant": {
                        "type": "string",
                        "description": f"Tenant slug (default: {DEFAULT_TENANT_SLUG})",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look ahead (default: 30)",
                    },
                },
            },
        ),
        types.Tool(
            name="get_sales",
            description="Get sales with optional date filtering and status filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant": {
                        "type": "string",
                        "description": f"Tenant slug (default: {DEFAULT_TENANT_SLUG})",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (ISO format: YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (ISO format: YYYY-MM-DD)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status: pending, assigned, in_transit, delivered, cancelled",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                    },
                },
            },
        ),
        types.Tool(
            name="get_sale_detail",
            description="Get detailed information about a specific sale including all items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sale_id": {
                        "type": "string",
                        "description": "Sale ID (MongoDB ObjectId)",
                    },
                    "tenant": {
                        "type": "string",
                        "description": f"Tenant slug (default: {DEFAULT_TENANT_SLUG})",
                    },
                },
                "required": ["sale_id"],
            },
        ),
        types.Tool(
            name="get_inbound_orders",
            description="Get inbound purchase orders with optional status filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant": {
                        "type": "string",
                        "description": f"Tenant slug (default: {DEFAULT_TENANT_SLUG})",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status: pending, received, paid",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                    },
                },
            },
        ),
        types.Tool(
            name="get_wastage",
            description="Get wastage records (product losses) with optional filtering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant": {
                        "type": "string",
                        "description": f"Tenant slug (default: {DEFAULT_TENANT_SLUG})",
                    },
                    "product_id": {
                        "type": "string",
                        "description": "Filter by product ID",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Filter by reason: vencido, dañado, perdido, robo, otro",
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (ISO format: YYYY-MM-DD)",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (ISO format: YYYY-MM-DD)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                    },
                },
            },
        ),
        types.Tool(
            name="get_dashboard_stats",
            description="Get dashboard statistics including total products, low stock count, pending orders, and recent sales.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tenant": {
                        "type": "string",
                        "description": f"Tenant slug (default: {DEFAULT_TENANT_SLUG})",
                    },
                },
            },
        ),
        types.Tool(
            name="list_tenants",
            description="List all available tenants in the system.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution"""

    if arguments is None:
        arguments = {}

    try:
        if name == "list_tenants":
            tenants = Tenant.objects.all()
            tenant_list = [
                {
                    "slug": t.slug,
                    "name": t.name,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in tenants
            ]
            return [
                types.TextContent(
                    type="text",
                    text=f"Found {len(tenant_list)} tenants:\n\n" +
                         "\n".join([f"- {t['name']} (slug: {t['slug']})" for t in tenant_list])
                )
            ]

        # Get tenant for all other operations
        tenant = get_tenant(arguments.get("tenant"))

        if name == "get_products":
            query = {"tenant": tenant}

            # Apply filters
            if "category" in arguments:
                query["category"] = arguments["category"]

            if "search" in arguments:
                search_term = arguments["search"]
                from mongoengine.queryset.visitor import Q
                query_obj = Product.objects(tenant=tenant).filter(
                    Q(name__icontains=search_term) | Q(sku__icontains=search_term)
                )
                products = list(query_obj)
            else:
                products = list(Product.objects(**query))

            # Filter by low stock if requested
            if arguments.get("low_stock_only"):
                products = [p for p in products if p.total_stock < p.critical_stock]

            serialized = [serialize_product(p) for p in products]

            return [
                types.TextContent(
                    type="text",
                    text=f"Found {len(serialized)} products for tenant '{tenant.slug}':\n\n" +
                         "\n".join([
                             f"- {p['name']} (SKU: {p['sku']}) - Stock: {p['total_stock']} - Price: ${p['base_price']:.2f}"
                             for p in serialized
                         ])
                )
            ]

        elif name == "get_product_detail":
            from bson import ObjectId
            product = Product.objects(id=ObjectId(arguments["product_id"]), tenant=tenant).first()
            if not product:
                return [types.TextContent(type="text", text="Product not found")]

            result = serialize_product(product)

            # Add lot information
            lots = [serialize_lot(lot) for lot in product.lots if lot.quantity_current > 0]
            result["lots"] = lots

            # Add bundle components if applicable
            if product.is_bundle:
                components = []
                for comp in ProductBundle.objects(bundle=product, tenant=tenant):
                    components.append({
                        "component_name": comp.component.name if comp.component else None,
                        "component_id": str(comp.component.id) if comp.component else None,
                        "quantity": comp.quantity,
                    })
                result["bundle_components"] = components

            details = f"""Product Details for '{product.name}':
- SKU: {result['sku']}
- Category: {result['category']}
- Base Price: ${result['base_price']:.2f}
- Total Stock: {result['total_stock']}
- Critical Stock Level: {result['critical_stock']}
- Is Bundle: {result['is_bundle']}

Available Lots ({len(lots)}):
""" + "\n".join([f"  - {lot['lot_code']}: {lot['quantity_current']} units (expires: {lot['expiry_date']})" for lot in lots])

            if result.get("bundle_components"):
                details += f"\n\nBundle Components ({len(result['bundle_components'])}):\n"
                details += "\n".join([
                    f"  - {comp['component_name']}: {comp['quantity']} units"
                    for comp in result["bundle_components"]
                ])

            return [types.TextContent(type="text", text=details)]

        elif name == "get_lots":
            query = {"tenant": tenant}

            if "product_id" in arguments:
                from bson import ObjectId
                product = Product.objects(id=ObjectId(arguments["product_id"]), tenant=tenant).first()
                if product:
                    query["product"] = product

            lots = list(Lot.objects(**query))

            if arguments.get("available_only"):
                lots = [lot for lot in lots if lot.quantity_current > 0]

            serialized = [serialize_lot(lot) for lot in lots]

            return [
                types.TextContent(
                    type="text",
                    text=f"Found {len(serialized)} lots for tenant '{tenant.slug}':\n\n" +
                         "\n".join([
                             f"- {lot['lot_code']} - {lot['product_name']}: {lot['quantity_current']}/{lot['quantity_initial']} units (expires: {lot['expiry_date']})"
                             for lot in serialized
                         ])
                )
            ]

        elif name == "get_expiring_products":
            days = arguments.get("days", 30)
            expiry_threshold = datetime.now() + timedelta(days=days)

            lots = Lot.objects(
                tenant=tenant,
                expiry_date__lte=expiry_threshold,
                quantity_current__gt=0
            ).order_by('expiry_date')

            expiring_products = {}
            for lot in lots:
                product_name = lot.product.name if lot.product else "Unknown"
                if product_name not in expiring_products:
                    expiring_products[product_name] = []
                expiring_products[product_name].append(serialize_lot(lot))

            result = f"Products expiring within {days} days for tenant '{tenant.slug}':\n\n"
            for product_name, product_lots in expiring_products.items():
                result += f"\n{product_name}:\n"
                for lot in product_lots:
                    result += f"  - Lot {lot['lot_code']}: {lot['quantity_current']} units (expires: {lot['expiry_date']})\n"

            return [types.TextContent(type="text", text=result)]

        elif name == "get_sales":
            query = {"tenant": tenant}

            if "status" in arguments:
                query["status"] = arguments["status"]

            sales = list(Sale.objects(**query).order_by('-date_created'))

            # Apply date filtering if provided
            if "start_date" in arguments:
                start = datetime.fromisoformat(arguments["start_date"])
                sales = [s for s in sales if s.date_created >= start]

            if "end_date" in arguments:
                end = datetime.fromisoformat(arguments["end_date"])
                sales = [s for s in sales if s.date_created <= end]

            # Apply limit
            limit = arguments.get("limit", 50)
            sales = sales[:limit]

            result = f"Found {len(sales)} sales for tenant '{tenant.slug}':\n\n"
            for sale in sales:
                items_count = len(list(sale.items))
                result += f"- Sale #{str(sale.id)[-6:]}: {sale.customer_name} - {items_count} items - Status: {sale.status} - Date: {sale.date_created.strftime('%Y-%m-%d')}\n"

            return [types.TextContent(type="text", text=result)]

        elif name == "get_sale_detail":
            from bson import ObjectId
            sale = Sale.objects(id=ObjectId(arguments["sale_id"]), tenant=tenant).first()
            if not sale:
                return [types.TextContent(type="text", text="Sale not found")]

            serialized = serialize_sale(sale)

            details = f"""Sale Details:
- Customer: {serialized['customer_name']}
- Address: {serialized['address']}
- Phone: {serialized['phone']}
- Status: {serialized['status']}
- Delivery Status: {serialized['delivery_status']}
- Payment Method: {serialized['payment_method']}
- Payment Confirmed: {serialized['payment_confirmed']}
- Date: {serialized['date_created']}

Items ({len(serialized['items'])}):
""" + "\n".join([
    f"  - {item['product_name']}: {item['quantity']} x ${item['unit_price']:.2f} = ${item['subtotal']:.2f}"
    for item in serialized['items']
])

            total = sum(item['subtotal'] for item in serialized['items'])
            details += f"\n\nTotal: ${total:.2f}"

            return [types.TextContent(type="text", text=details)]

        elif name == "get_inbound_orders":
            query = {"tenant": tenant}

            if "status" in arguments:
                query["status"] = arguments["status"]

            orders = list(InboundOrder.objects(**query).order_by('-created_at'))

            limit = arguments.get("limit", 50)
            orders = orders[:limit]

            serialized = [serialize_inbound_order(o) for o in orders]

            result = f"Found {len(serialized)} inbound orders for tenant '{tenant.slug}':\n\n"
            for order in serialized:
                result += f"- {order['supplier_name']} - Invoice: {order['invoice_number']} - Status: {order['status']} - Total: ${order['total']:.2f}\n"

            return [types.TextContent(type="text", text=result)]

        elif name == "get_wastage":
            query = {"tenant": tenant}

            if "product_id" in arguments:
                from bson import ObjectId
                product = Product.objects(id=ObjectId(arguments["product_id"]), tenant=tenant).first()
                if product:
                    query["product"] = product

            if "reason" in arguments:
                query["reason"] = arguments["reason"]

            wastage_records = list(Wastage.objects(**query).order_by('-date_created'))

            # Apply date filtering
            if "start_date" in arguments:
                start = datetime.fromisoformat(arguments["start_date"])
                wastage_records = [w for w in wastage_records if w.date_created >= start]

            if "end_date" in arguments:
                end = datetime.fromisoformat(arguments["end_date"])
                wastage_records = [w for w in wastage_records if w.date_created <= end]

            limit = arguments.get("limit", 50)
            wastage_records = wastage_records[:limit]

            serialized = [serialize_wastage(w) for w in wastage_records]

            result = f"Found {len(serialized)} wastage records for tenant '{tenant.slug}':\n\n"
            for wastage in serialized:
                result += f"- {wastage['product_name']}: {wastage['quantity']} units - Reason: {wastage['reason']} - Date: {wastage['date_created']}\n"

            return [types.TextContent(type="text", text=result)]

        elif name == "get_dashboard_stats":
            # Get stats
            total_products = Product.objects(tenant=tenant).count()

            low_stock_products = [
                p for p in Product.objects(tenant=tenant)
                if p.total_stock < p.critical_stock
            ]
            low_stock_count = len(low_stock_products)

            pending_orders = InboundOrder.objects(tenant=tenant, status="pending").count()

            # Recent sales (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_sales = Sale.objects(tenant=tenant, date_created__gte=week_ago).count()

            # Total stock value (approximation)
            total_value = 0.0
            for product in Product.objects(tenant=tenant):
                total_value += product.total_stock * float(product.base_price or 0)

            stats = f"""Dashboard Statistics for '{tenant.slug}':

Products:
- Total Products: {total_products}
- Low Stock Alerts: {low_stock_count}
- Total Inventory Value: ${total_value:,.2f}

Orders:
- Pending Inbound Orders: {pending_orders}

Sales:
- Sales (Last 7 Days): {recent_sales}

Low Stock Products:
""" + "\n".join([f"  - {p.name}: {p.total_stock}/{p.critical_stock} units" for p in low_stock_products[:10]])

            if low_stock_count > 10:
                stats += f"\n  ... and {low_stock_count - 10} more"

            return [types.TextContent(type="text", text=stats)]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the MCP server"""
    # Setup logging to file (not stdout/stderr which are used by MCP)
    log_file = "/tmp/sipud_mcp_server.log"

    def log(message):
        with open(log_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")

    log("=== SIPUD MCP Server Starting ===")

    # Connect to MongoDB
    try:
        connect(
            db=MONGODB_DB,
            host=MONGODB_HOST,
            port=MONGODB_PORT,
        )
        log(f"Connected to MongoDB: {MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}")
        print(f"Connected to MongoDB: {MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}", file=sys.stderr)
    except Exception as e:
        log(f"Failed to connect to MongoDB: {e}")
        print(f"Failed to connect to MongoDB: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # Run the server using stdin/stdout streams
        log("Starting MCP server with stdio...")
        async with stdio_server() as (read_stream, write_stream):
            log("stdio_server initialized, running server.run()...")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="sipud-inventory",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        log("MCP server finished normally")
    except Exception as e:
        log(f"Error running MCP server: {e}")
        log(f"Error type: {type(e)}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        # Disconnect from MongoDB
        log("Disconnecting from MongoDB...")
        disconnect()
        log("=== SIPUD MCP Server Stopped ===")


if __name__ == "__main__":
    asyncio.run(main())
