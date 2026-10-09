import logging
from typing import Any, Optional

logger = logging.getLogger("markazi.schema")

SERVICE_IS = "IS (Inventory/Operations - Schema 'public')"
SERVICE_US = "US (User & Access Management - Schema 'us')"
SERVICE_LS = "LS (License & Billing - Schema 'ls')"
SERVICE_TECH = "Technical & Maintenance (Schema 'public')"

# ==============================================================================
# 1. COLUMN-LEVEL SEMANTIC KNOWLEDGE BASE
# Explains exact business meaning, quirks, and formulas for individual columns.
# ==============================================================================
COLUMN_SEMANTIC_NOTES: dict[str, str] = {
    # --- public.location ---
    "location.id": "Primary key of warehouse/store location (int4)",
    "location.name": "Facility title e.g. 'General Warehouse - AF', 'Main Hub'",
    "location.sourceId": "External ERP warehouse identifier code",
    "location.warehouseSourceId": "ERP warehouse source mapping code",
    "location.type": "Type of facility (e.g. WAREHOUSE, RETAIL_STORE, DISTRIBUTION_HUB)",
    "location.isActive": "Operational status flag (true = active/open, false = inactive/closed)",
    "location.isConfigured": "Configuration readiness boolean flag",
    "location.address": "Street address / physical address of facility",
    "location.companyId": "FK to public.company.id (owning parent company)",
    "location.parentId": "Self-referencing FK to public.location.id for sub-zones/sub-warehouses",

    # --- public.order ---
    "order.id": "Primary key of order (int4)",
    "order.orderNo": "Unique customer order reference / tracking number (varchar)",
    "order.inventorySourceOrderNo": "Order number in external source system / ecommerce platform",
    "order.erpInvoiceToPayNo": "Connected ERP invoice / voucher number",
    "order.orderSource": "Origin channel enum (SHOPIFY, WOOCOMMERCE, AMAZON, DARAZ, OTHER)",
    "order.paymentMethod": "Payment mode e.g. 'COD', 'Credit Card', 'BOGUS'",
    "order.consignmentNo": "Courier air waybill (AWB) / tracking number",
    "order.city": "Customer destination delivery city (e.g. Lahore, Karachi, Islamabad). CRITICAL: City is here, NOT in location!",
    "order.currency": "Transaction currency code e.g. 'PKR', 'USD'",
    "order.customerName": "Customer full name",
    "order.customerPhone": "Customer contact telephone number",
    "order.customerEmail": "Customer email address",
    "order.customerAddress": "Full destination shipping street address",
    "order.actualAmount": "Gross order subtotal before discounts and shipping (numeric)",
    "order.discount": "Discount amount deducted from order (numeric)",
    "order.shippingFee": "Delivery / courier shipping charges added to order (numeric)",
    "order.finalAmount": "Net total payable by customer = actualAmount - discount + shippingFee (numeric)",
    "order.status": "Current lifecycle status enum (PENDING, CONFIRMED, PACKING, PACKED, DISPATCHED, DELIVERED, RETURNED_BY_CUSTOMER, RETURNED_BY_COURIER, CANCELLED, ON_HOLD)",
    "order.returnOrderStatus": "Return handling status enum (PENDING, IN_PROGRESS, READY_FOR_RESTOCK, RETURNED)",
    "order.warehouse_id": "FK to public.location.id - Physical warehouse from which order is dispatched",
    "order.courierId": "FK to public.courier.id - Logistics carrier delivering order (e.g. DHL, blueex)",
    "order.courierPersonId": "FK to public.courier_person.id - Assigned delivery rider / person",
    "order.channelId": "FK to public.channel.id - Sales channel where order originated (Shopify, WooCommerce)",
    "order.isDuplicate": "Boolean flag indicating duplicate order detection",
    "order.createdByName": "Name of user/operator or channel system who created order",

    # --- public.order_item ---
    "order_item.id": "Primary key of line item (int4)",
    "order_item.orderId": "FK to public.\"order\".id - Parent order",
    "order_item.variantId": "FK to public.product_variant.id - Specific ordered variant/SKU",
    "order_item.quantity": "Quantity of units ordered (int4)",
    "order_item.unitPrice": "Price per single unit (numeric)",
    "order_item.totalPrice": "Total line price = quantity * unitPrice (numeric)",
    "order_item.discountAmount": "Discount amount deducted for this item",
    "order_item.itemState": "Physical condition enum (GOOD, DAMAGED, MISSING)",
    "order_item.isScanned": "Barcode scan verification boolean during packing",
    "order_item.isRequestedForReturn": "Boolean flag indicating return request",

    # --- public.order_activity ---
    "order_activity.id": "Primary key of audit event (int4)",
    "order_activity.orderId": "FK to public.\"order\".id",
    "order_activity.status": "Status reached at this event (CONFIRMED, PACKING, PACKED, DISPATCHED, DELIVERED, CANCELLED, etc.)",
    "order_activity.activityAt": "Exact timestamp when status transition occurred",
    "order_activity.activityByName": "Operator / user name who triggered transition",

    # --- public.stock ---
    "stock.id": "Primary key of inventory entry (int4)",
    "stock.onHand": "Physical inventory physically present in warehouse (numeric)",
    "stock.reserved": "Inventory allocated/locked for pending orders (numeric)",
    "stock.available": "Available stock ready for new sales = COALESCE(available, onHand - reserved, 0) (numeric)",
    "stock.product": "FK to public.product_variant.id - Specific product variant SKU",
    "stock.location": "FK to public.location.id - Physical warehouse location",
    "stock.sourceId": "ERP inventory ledger reference code",

    # --- public.product & product_variant ---
    "product.id": "Primary key of master product (int4)",
    "product.title": "General master product title e.g. 'Wire', 'Shoes'",
    "product_variant.id": "Primary key of sellable SKU variant (int4)",
    "product_variant.sku": "Unique Stock Keeping Unit identifier e.g. 'FG0070'",
    "product_variant.title": "Variant title e.g. 'Wire # 14 Hot Willai'",
    "product_variant.barCode": "Scannable product barcode",
    "product_variant.product": "Nullable FK to public.product.id (master product). Standalone SKUs have NULL; always use LEFT JOIN!",

    # --- public.product_price & price_list ---
    "price_list.id": "Primary key of price tier catalog (int4)",
    "price_list.title": "Price tier title e.g. 'Retail', 'Wholesale'",
    "product_price.price": "Selling rate in this price list (numeric)",
    "product_price.productVariant": "FK to public.product_variant.id",
    "product_price.priceList": "FK to public.price_list.id",

    # --- public.channel & courier ---
    "channel.channelName": "Storefront platform name e.g. 'SHOPIFY', 'WOOCOMMERCE'",
    "channel.isAddon": "Boolean flag indicating addon subscription status",
    "channel.partnerId": "FK to public.partner.id",
    "courier.courierName": "Logistics carrier name e.g. 'DHL', 'blueex'",
    "courier.partnerId": "FK to public.partner.id",
    "courier_person.name": "Delivery rider / courier person full name",

    # --- public.company & company_closure ---
    "company.title": "Company / brand / organization legal title",
    "company.isActive": "Company active status boolean",
    "company.parentId": "Self-referencing FK to public.company.id for parent holding company",
    "company_closure.id_ancestor": "FK to public.company.id (parent/ancestor company)",
    "company_closure.id_descendant": "FK to public.company.id (child/subsidiary company)",

    # --- public.journal & payment_settings ---
    "journal.name": "Accounting journal / ledger title (e.g. Sales Journal, Cash Book)",
    "journal.company": "FK to public.company.id",
    "payment_settings.direction": "Payment direction (INBOUND, OUTBOUND)",
    "payment_settings.journal": "FK to public.journal.id",

    # --- us.users ---
    "users.id": "Primary key of user account (int4)",
    "users.staffId": "Employee badge / staff ID code e.g. 'STF-003'",
    "users.name": "Staff / employee full name",
    "users.email": "User login email address",
    "users.cellNo": "Contact phone number",
    "users.gender": "Gender enum (MALE, FEMALE, OTHER)",
    "users.dob": "Date of birth (date)",
    "users.locationId": "CRITICAL: Foreign link to public.location.id - Physical warehouse/store where staff is stationed",
    "users.roleId": "FK to us.roles.id - Security role and job designation",
    "users.isActive": "Active employee status boolean (true = currently employed/active)",
    "users.isPlatformAdmin": "System superadministrator boolean flag",
    "users.isVendorAdmin": "Merchant organization admin boolean flag",

    # --- us.roles & permissions ---
    "roles.id": "Primary key of role (int4)",
    "roles.title": "Role title / job designation e.g. 'Test Admin', 'Warehouse Operator'",
    "roles.isActive": "Role active status boolean",
    "permissions.module": "Functional module grouping name (Inventory, Orders, Users)",
    "permissions.permission": "Human-readable permission title",
    "permissions.slug": "Unique permission programmatic identifier slug",
    "role_permissions.role": "FK to us.roles.id",
    "role_permissions.slug": "Logical FK to us.permissions.slug",

    # --- us.widgets & theme_settings ---
    "widgets.userId": "FK to us.users.id (owner of dashboard widget)",
    "widgets.key": "Dashboard metric key identifier",
    "theme_settings.brandColorsSettings": "JSONB brand visual theme colors configuration",

    # --- ls.license ---
    "license.id": "Primary key of software subscription license (int4)",
    "license.configuration": "TEXT column containing JSON with tenant limits: noOfWarehouseAllowed, noOfStaffAllowed, noOfOrdersProcessingAllowed, erp, salesChannels, courierPartners. MUST cast with ::json!",

    # --- ls.invoice ---
    "invoice.id": "Primary key of billing invoice (int4)",
    "invoice.invoiceNo": "Invoice reference number e.g. 'INV-1001'",
    "invoice.status": "Invoice payment status enum (PAID, PENDING, DRAFT, EXPIRED)",
    "invoice.billedLicense": "JSONB snapshot breakdown of billed license features"
}

# ==============================================================================
# 2. IN-DEPTH TABLE PURPOSE KNOWLEDGE
# Covers every table with deep explanation, column concepts, synonyms, rules & join patterns.
# ==============================================================================
TABLE_PURPOSE_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "company": {
        "service": SERVICE_IS,
        "description": "Stores companies, business entities, and brands in a multi-tenant hierarchy. Serves as top-level root for locations, warehouses, journals, and financial accounts.",
        "concepts": "id = company ID, title = company name, isActive = active status, sourceId = external ERP ID, parentId = parent holding company FK.",
        "synonyms": "company, companies, brand, organization, merchant, enterprise, idara, parent company, child company, sister company, business entity",
        "rules": "To find child subsidiaries of a parent company, query WHERE parentId = <id>. For full company hierarchy tree traversal, query public.company_closure.",
        "join_hints": [
            "JOIN public.location ON location.\"companyId\" = company.id -- Warehouses belonging to company",
            "JOIN public.journal ON journal.company = company.id -- Financial accounting journals of company",
            "LEFT JOIN public.company parent ON company.\"parentId\" = parent.id -- Parent holding company"
        ]
    },
    "company_closure": {
        "service": SERVICE_IS,
        "description": "Transitive closure table for high-speed hierarchical querying of parent-child company organizational trees.",
        "concepts": "id_ancestor = parent/ancestor company FK, id_descendant = child/descendant company FK.",
        "synonyms": "company hierarchy, company tree, ancestor company, descendant company, parent child closure, shijra nasab, org structure",
        "rules": "Use id_ancestor = <id> to retrieve all child, sub-child, and descendant companies without recursive CTEs.",
        "join_hints": [
            "JOIN public.company anc ON company_closure.id_ancestor = anc.id",
            "JOIN public.company desc_comp ON company_closure.id_descendant = desc_comp.id"
        ]
    },
    "location": {
        "service": SERVICE_IS,
        "description": "Stores physical warehouses, distribution centers, godowns, fulfillment hubs, and retail store branches where inventory is physically kept.",
        "concepts": "id = location ID, name = warehouse/store title, sourceId = ERP warehouse code, warehouseSourceId = warehouse mapping code, type = facility type, address = street address, latitude/longitude = GPS, isActive = operational flag, isConfigured = config readiness, companyId = parent company FK, parentId = parent zone FK.",
        "synonyms": "warehouse, godown, store, location, depot, branch, fulfillment center, dukan, karkhana, maal ka kamra, physical location, inventory hub",
        "rules": "CRITICAL: Table location does NOT have a 'city' column! Never write location.city (city is in \"order\".city). Use location.name or location.address. To find active warehouses: WHERE location.\"isActive\" = true. Cross-service link: us.users.\"locationId\" = location.id.",
        "join_hints": [
            "JOIN us.users ON us.users.\"locationId\" = location.id -- Staff/employees stationed at warehouse",
            "JOIN public.stock ON stock.location = location.id -- Inventory quantities in warehouse",
            "JOIN public.\"order\" ON \"order\".\"warehouse_id\" = location.id -- Orders dispatched from warehouse",
            "JOIN public.company ON location.\"companyId\" = company.id -- Company owning warehouse"
        ]
    },
    "product": {
        "service": SERVICE_IS,
        "description": "Stores high-level master product definitions (e.g. 'Wire', 'Cotton T-Shirt'). Parent header entity; actual sellable SKUs with barcodes and sizes are in product_variant.",
        "concepts": "id = master product ID, title = product name, sourceId = ERP master product code.",
        "synonyms": "product, master product, products, items, general product, saman, cheez, maal, product category, parent product",
        "rules": "Master products are parent headers. Orders and stock ALWAYS link to product_variant! Since product_variant.product is nullable, ALWAYS use LEFT JOIN public.product p ON p.id = pv.product.",
        "join_hints": [
            "JOIN public.product_variant pv ON pv.product = product.id -- Sellable SKUs of master product"
        ]
    },
    "product_variant": {
        "service": SERVICE_IS,
        "description": "Stores individual sellable product variants and SKUs (e.g. 'Wire # 14 Hot Willai', 'Nike Shoes Black Size 42') with SKU code, barcode, and images.",
        "concepts": "id = variant ID, sku = unique SKU code (e.g. 'FG0070'), title = variant title, barCode = EAN/UPC barcode, sourceId = ERP item code, product = nullable FK to master product.id.",
        "synonyms": "product variant, variant, SKU, barcode, size, color, sellable item, specific item, variant specs, item code, maal ka variant",
        "rules": "product FK is nullable! Standalone SKUs have NULL product. ALWAYS use LEFT JOIN public.product p ON p.id = pv.product. Resolved product name: COALESCE(p.title, pv.title, pv.sku) AS product_name.",
        "join_hints": [
            "LEFT JOIN public.product p ON p.id = product_variant.product -- Parent master product",
            "JOIN public.stock s ON s.product = product_variant.id -- Inventory of this SKU",
            "JOIN public.order_item oi ON oi.\"variantId\" = product_variant.id -- Ordered line items",
            "JOIN public.product_price pp ON pp.\"productVariant\" = product_variant.id -- Prices"
        ]
    },
    "price_list": {
        "service": SERVICE_IS,
        "description": "Stores pricing catalogs and rate lists (e.g. 'Retail', 'Wholesale', 'Distributor Rate') allowing multi-tier customer pricing.",
        "concepts": "id = price list ID, title = tier title, sourceId = ERP price tier code.",
        "synonyms": "price list, rate list, wholesale rate, retail price, price tiers, customer rate catalog, nirkh nama, keemat list",
        "rules": "Connects to product_variant through product_price junction table.",
        "join_hints": [
            "JOIN public.product_price ON product_price.\"priceList\" = price_list.id"
        ]
    },
    "product_price": {
        "service": SERVICE_IS,
        "description": "Junction table storing prices of product variants across different price lists (product_variant <-> product_price <-> price_list).",
        "concepts": "id = price ID, price = numerical price amount, productVariant = FK to product_variant.id, priceList = FK to price_list.id.",
        "synonyms": "product price, variant price, selling price, rate, qeemat, keemat, cost, price tag, item rate",
        "rules": "Wrap camelCase columns in double quotes: \"productVariant\", \"priceList\".",
        "join_hints": [
            "JOIN public.product_variant pv ON product_price.\"productVariant\" = pv.id",
            "JOIN public.price_list pl ON product_price.\"priceList\" = pl.id"
        ]
    },
    "stock": {
        "service": SERVICE_IS,
        "description": "Stores real-time inventory balances of product variants across warehouse locations. Tracks physical onHand, reserved for orders, and net available stock.",
        "concepts": "id = stock ID, onHand = physical stock count, reserved = stock locked for active orders, available = net available stock, product = FK to product_variant.id, location = FK to location.id.",
        "synonyms": "stock, inventory, maal, godown maal, bacha hua maal, onHand, reserved, available, balance, kitna saman bacha, stock quantity, stock balance, warehouse inventory, dukan ka maal",
        "rules": "Available stock calculation formula: COALESCE(stock.\"available\", stock.\"onHand\" - stock.\"reserved\", 0). Out of stock filter: WHERE COALESCE(stock.\"available\", stock.\"onHand\" - stock.\"reserved\", 0) <= 0. To see stock per warehouse: JOIN public.location l ON stock.location = l.id.",
        "join_hints": [
            "JOIN public.product_variant pv ON stock.product = pv.id -- Variant details",
            "LEFT JOIN public.product p ON pv.product = p.id -- Master product details",
            "JOIN public.location l ON stock.location = l.id -- Warehouse location"
        ]
    },
    "order": {
        "service": SERVICE_IS,
        "description": "Primary sales order and customer fulfillment table. Tracks order numbers, customer details, shipping destinations, financial totals (actualAmount, discount, shippingFee, finalAmount), order statuses, channels, couriers, and warehouses.",
        "concepts": "id = order ID, orderNo = order number, city = shipping city, customerName = customer name, customerPhone = phone, customerEmail = email, customerAddress = address, actualAmount = gross sum, discount = discount, shippingFee = delivery fee, finalAmount = net total, status = order lifecycle enum (PENDING, CONFIRMED, PACKING, PACKED, DISPATCHED, DELIVERED, RETURNED_BY_CUSTOMER, RETURNED_BY_COURIER, CANCELLED, ON_HOLD), warehouse_id = fulfillment warehouse FK, courierId = courier FK, courierPersonId = rider FK, channelId = sales channel FK.",
        "synonyms": "order, orders, sales, customer order, consignment, booking, bikri, khareed, customer details, revenue, turnover, parcel, shipment, parcel status",
        "rules": "CRITICAL: Table name MUST be quoted: public.\"order\" or \"order\" (SQL reserved keyword). Wrap camelCase columns in double quotes: \"orderNo\", \"finalAmount\", \"actualAmount\", \"shippingFee\", \"discount\", \"customerName\", \"customerPhone\", \"customerAddress\", \"warehouse_id\", \"courierId\", \"channelId\", \"courierPersonId\", \"orderSource\". Net Revenue / Sales Formula: ALWAYS exclude cancelled and returned orders: WHERE \"order\".\"status\"::text NOT IN ('CANCELLED', 'RETURNED_BY_CUSTOMER', 'RETURNED_BY_COURIER'). Delivered Orders: WHERE \"order\".\"status\"::text = 'DELIVERED'.",
        "join_hints": [
            "JOIN public.order_item oi ON oi.\"orderId\" = \"order\".id -- Line items in order",
            "JOIN public.order_activity oa ON oa.\"orderId\" = \"order\".id -- Status event audit trail",
            "LEFT JOIN public.location l ON \"order\".\"warehouse_id\" = l.id -- Fulfillment warehouse",
            "LEFT JOIN public.courier c ON \"order\".\"courierId\" = c.id -- Courier shipping provider",
            "LEFT JOIN public.courier_person cp ON \"order\".\"courierPersonId\" = cp.id -- Delivery rider",
            "LEFT JOIN public.channel ch ON \"order\".\"channelId\" = ch.id -- Sales channel (Shopify, WooCommerce)"
        ]
    },
    "order_item": {
        "service": SERVICE_IS,
        "description": "Stores individual line items ordered inside customer orders. Connects order to product variant with quantity, unitPrice, totalPrice, discounts, and item physical condition (itemState).",
        "concepts": "id = line item ID, orderId = FK to \"order\".id, variantId = FK to product_variant.id, quantity = count, unitPrice = rate, totalPrice = quantity * unitPrice, discountAmount = discount, itemState = condition enum (GOOD, DAMAGED, MISSING), isScanned = packing scan flag.",
        "synonyms": "order item, order items, line items, ordered items, item details, quantity ordered, unitPrice, totalPrice, saman ki detail, order ke items",
        "rules": "To query best-selling products: GROUP BY variantId or product title and ORDER BY SUM(oi.quantity) DESC. When calculating revenue per item, exclude cancelled orders.",
        "join_hints": [
            "JOIN public.\"order\" o ON order_item.\"orderId\" = o.id -- Parent order",
            "JOIN public.product_variant pv ON order_item.\"variantId\" = pv.id -- Variant details",
            "LEFT JOIN public.product p ON pv.product = p.id -- Master product details"
        ]
    },
    "order_activity": {
        "service": SERVICE_IS,
        "description": "Chronological audit trail and timeline of order lifecycle status changes (CONFIRMED, PACKING, PACKED, DISPATCHED, DELIVERED, CANCELLED). Records timestamp and operator who performed each change.",
        "concepts": "id = activity ID, orderId = FK to \"order\".id, status = status transition enum, activityAt = exact timestamp, activityByName = operator name.",
        "synonyms": "order activity, order timeline, order history, audit trail, order status changes, timeline log, tareekh, kis ne kab status badla, tracking logs",
        "rules": "Use when user asks 'when was order X delivered/packed/dispatched' or 'who changed status of order X'.",
        "join_hints": [
            "JOIN public.\"order\" o ON order_activity.\"orderId\" = o.id"
        ]
    },
    "courier": {
        "service": SERVICE_IS,
        "description": "Stores shipping and delivery courier logistics companies (e.g. DHL, blueex, TCS, Leopards) used for delivering customer orders.",
        "concepts": "id = courier ID, courierName = carrier title (e.g. 'DHL', 'blueex'), configuration = API credentials JSONB, partnerId = FK to partner.id.",
        "synonyms": "courier, shipping partner, delivery company, DHL, blueex, TCS, Leopards, logistics carrier, parcel service, dak khana",
        "rules": "Wrap \"courierName\" in double quotes. Live database courier names: 'DHL', 'blueex'.",
        "join_hints": [
            "JOIN public.\"order\" ON \"order\".\"courierId\" = courier.id -- Orders dispatched via courier",
            "JOIN public.partner ON courier.\"partnerId\" = partner.id"
        ]
    },
    "courier_person": {
        "service": SERVICE_IS,
        "description": "Stores individual delivery riders, dispatch boys, or courier persons assigned to deliver shipments to customers.",
        "concepts": "id = rider ID, name = rider full name, documentUrl = rider verification document URL.",
        "synonyms": "courier person, rider, delivery boy, dispatch rider, driver, courier agent, delivery person, qasid",
        "rules": "Connects to \"order\" via \"order\".\"courierPersonId\" = courier_person.id.",
        "join_hints": [
            "JOIN public.\"order\" ON \"order\".\"courierPersonId\" = courier_person.id"
        ]
    },
    "channel": {
        "service": SERVICE_IS,
        "description": "Stores sales channels and ecommerce platforms (e.g. Shopify, WooCommerce, Amazon, Daraz) where customer orders are received.",
        "concepts": "id = channel ID, channelName = channel title (e.g. 'SHOPIFY', 'WOOCOMMERCE'), configuration = store credentials JSONB, isAddon = addon flag, partnerId = FK to partner.id.",
        "synonyms": "channel, sales channel, shopify, woocommerce, web store, online store, marketplace, order source, daraz, amazon, bikri ka zariya",
        "rules": "Wrap \"channelName\" in double quotes. Live database channels: 'SHOPIFY', 'WOOCOMMERCE'.",
        "join_hints": [
            "JOIN public.\"order\" ON \"order\".\"channelId\" = channel.id -- Orders from channel",
            "JOIN public.partner ON channel.\"partnerId\" = partner.id"
        ]
    },
    "partner": {
        "service": SERVICE_IS,
        "description": "Stores external integration and business partners associated with courier services and sales storefront channels.",
        "concepts": "id = partner ID, name = partner title, sourceId = external partner code.",
        "synonyms": "partner, business partner, integration partner, vendor, third party partner",
        "rules": "Referenced by courier.\"partnerId\" and channel.\"partnerId\".",
        "join_hints": [
            "JOIN public.courier ON courier.\"partnerId\" = partner.id",
            "JOIN public.channel ON channel.\"partnerId\" = partner.id"
        ]
    },
    "erp": {
        "service": SERVICE_IS,
        "description": "Stores connected Enterprise Resource Planning (ERP) integrations (e.g. SAP Business One, Oracle) and synchronization connectivity status.",
        "concepts": "id = erp ID, erpName = ERP software name (e.g. 'SAP'), configuration = connection params JSONB, isConnected = live connection boolean.",
        "synonyms": "erp, enterprise resource planning, SAP, SAP B1, accounting ERP, core system, system integration",
        "rules": "Wrap \"erpName\" and \"isConnected\" in double quotes.",
        "join_hints": []
    },
    "journal": {
        "service": SERVICE_IS,
        "description": "Stores financial general ledger accounting journals and books (Sales Journal, Purchase Journal, Bank, Cash) linked to companies.",
        "concepts": "id = journal ID, name = journal title, code = GL account code, type = journal classification, sourceId, company = FK to company.id.",
        "synonyms": "journal, general ledger, accounting journal, financial books, rooznamcha, accounts ledger, khata",
        "rules": "Connects to company via journal.company = company.id.",
        "join_hints": [
            "JOIN public.company ON journal.company = company.id",
            "JOIN public.payment_settings ON payment_settings.journal = journal.id"
        ]
    },
    "payment_settings": {
        "service": SERVICE_IS,
        "description": "Stores payment configuration and mapping rules connecting payment gateway modes with financial accounting journals.",
        "concepts": "id = setting ID, name = payment mode title, direction = inbound/outbound, accountId = GL account code, journal = FK to journal.id.",
        "synonyms": "payment settings, payment mapping, payment gateway settings, cash configuration, adaigi ki settings",
        "rules": "Connects to journal via payment_settings.journal = journal.id.",
        "join_hints": [
            "JOIN public.journal ON payment_settings.journal = journal.id"
        ]
    },
    "notification": {
        "service": SERVICE_IS,
        "description": "Stores in-app notifications and alerts generated for users and order lifecycle events (CONFIRMED, PACKED, DISPATCH, DELIVERED, CANCELLED, RETURNED).",
        "concepts": "id = notification ID, title = notification subject, message = alert body, type = notification enum, receiverId = user recipient, isRead = read flag, createdByName = sender.",
        "synonyms": "notification, system alert, order alert, bell notification, ittila, pegham",
        "rules": "type is enum: ORDER_CONFIRMED, ORDER_ON_HOLD, ORDER_PACKING, ORDER_PACKED, ORDER_DISPATCH, ORDER_DELIVERED, ORDER_CANCELLED, ORDER_RETURNED.",
        "join_hints": []
    },
    "settings": {
        "service": SERVICE_IS,
        "description": "Stores global operational configuration policies (duplicate order detection rules, courier assignment logic, warehouse fulfillment settings).",
        "concepts": "duplicateOrderConfiguration, courierConfiguration, warehouseConfiguration.",
        "synonyms": "settings, platform settings, application preferences, configuration rules",
        "rules": "Contains technical configuration blocks, not transactional business data.",
        "join_hints": []
    },
    "system_log": {
        "service": SERVICE_IS,
        "description": "Stores technical API request/response audit logs for debugging, error monitoring, and performance diagnostics. Do not treat as transactional business data.",
        "concepts": "id, source, requestUrl, requestBody, response, created_at.",
        "synonyms": "system log, api log, request log, debug logs, error log",
        "rules": "Do NOT query unless user specifically asks for API logs, request errors, or technical debug logs.",
        "join_hints": []
    },
    "migration_table": {
        "service": SERVICE_TECH,
        "description": "Technical database migration tracker recording applied database version scripts. Not for business reporting.",
        "concepts": "id, timestamp, name.",
        "synonyms": "migrations, database migrations, schema history",
        "rules": "Excluded from normal business reporting.",
        "join_hints": []
    },

    # --- US SERVICE (User & Access Management - Schema 'us') ---
    "users": {
        "service": SERVICE_US,
        "description": "Stores system user accounts, employees, warehouse operators, staff, and platform administrators. Maps to security roles and assigned physical warehouse locations.",
        "concepts": "id = user ID, staffId = employee code (e.g. 'STF-003'), name = staff full name, email = login email, cellNo = contact number, gender = gender enum (MALE, FEMALE, OTHER), dob = birth date, locationId = FK to public.location.id (assigned warehouse/store), roleId = FK to us.roles.id (role/designation), isActive = active employee flag, isPlatformAdmin = superadmin flag.",
        "synonyms": "users, user, employee, staff, admin, operator, account, mulazim, bande, team member, profile, workers, staff member, kam karne wale",
        "rules": "Schema is 'us'. Explicit qualification recommended: us.users (or users). Wrap camelCase columns in double quotes: \"staffId\", \"locationId\", \"roleId\", \"isActive\", \"cellNo\", \"isPlatformAdmin\". CROSS-SERVICE LINK: us.users.\"locationId\" = public.location.id (links staff member to assigned physical warehouse). Active staff filter: WHERE us.users.\"isActive\" = true.",
        "join_hints": [
            "JOIN public.location l ON us.users.\"locationId\" = l.id -- Warehouse/branch where staff is stationed",
            "LEFT JOIN us.roles r ON us.users.\"roleId\" = r.id -- Role and designation of staff",
            "JOIN us.widgets w ON w.\"userId\" = us.users.id -- Dashboard widgets configured by user"
        ]
    },
    "roles": {
        "service": SERVICE_US,
        "description": "Stores user security roles and permission designations (e.g. 'Test Admin', 'Warehouse Operator', 'Staff Admin').",
        "concepts": "id = role ID, title = role designation title, description = role description, isActive = active role flag.",
        "synonyms": "roles, role, user role, designation, job title, position, access level, uhda, permissions role, mansab",
        "rules": "Schema is 'us'. Connects to users via us.users.\"roleId\" = us.roles.id. Connects to permissions via us.role_permissions.",
        "join_hints": [
            "JOIN us.users u ON u.\"roleId\" = roles.id -- Users holding this role",
            "JOIN us.role_permissions rp ON rp.role = roles.id -- Permissions granted to role"
        ]
    },
    "permissions": {
        "service": SERVICE_US,
        "description": "Stores granular system privilege definitions categorized by business module (e.g. Inventory, Orders, Users, Reports).",
        "concepts": "id = permission ID, module = module group name, permission = permission title, slug = unique permission identifier slug, description.",
        "synonyms": "permissions, permission, privileges, access rights, feature rights, module rights, permission slug, ikhtiyarat",
        "rules": "Schema is 'us'. Mapped to roles via us.role_permissions.slug = us.permissions.slug.",
        "join_hints": [
            "JOIN us.role_permissions rp ON rp.slug = permissions.slug"
        ]
    },
    "role_permissions": {
        "service": SERVICE_US,
        "description": "Junction table mapping security roles to assigned permission slugs (roles <-> role_permissions <-> permissions).",
        "concepts": "id = mapping ID, role = FK to us.roles.id, slug = logical link to us.permissions.slug.",
        "synonyms": "role permissions, role permission, assigned permissions, access mapping, role rights",
        "rules": "Schema is 'us'. Maps role to permission.",
        "join_hints": [
            "JOIN us.roles r ON role_permissions.role = r.id",
            "JOIN us.permissions p ON role_permissions.slug = p.slug"
        ]
    },
    "widgets": {
        "service": SERVICE_US,
        "description": "Stores personalized user dashboard analytics cards, metric widgets, and UI layout grid coordinates.",
        "concepts": "id = widget ID, userId = FK to us.users.id, title = card title, key = metric code, icon = icon name, xAxis, yAxis, height, width.",
        "synonyms": "widgets, widget, dashboard widget, dashboard card, metrics card, user layout, analytics card",
        "rules": "Schema is 'us'. Connects to owner user via us.widgets.\"userId\" = us.users.id.",
        "join_hints": [
            "JOIN us.users u ON widgets.\"userId\" = u.id"
        ]
    },
    "theme_settings": {
        "service": SERVICE_US,
        "description": "Stores tenant UI visual theme preferences, corporate logo URL, and brand color palette configuration.",
        "concepts": "id = theme ID, logo = branding logo image URL, brandColorsSettings = JSONB color scheme.",
        "synonyms": "theme settings, branding, brand colors, logo, appearance, ui theme",
        "rules": "Schema is 'us'. Stores branding config.",
        "join_hints": []
    },

    # --- LS SERVICE (License & Billing - Schema 'ls') ---
    "license": {
        "service": SERVICE_LS,
        "description": "Stores tenant software subscription license specifications, operational quota limits (allowed warehouses, allowed staff, monthly order processing quota), ERP connector config, and channel/courier addon allocations.",
        "concepts": "id = license ID, configuration = TEXT column containing JSON with tenant quotas: noOfWarehouseAllowed, noOfStaffAllowed, noOfOrdersProcessingAllowed, numberOfWarehousAddOns, numberOfStaffAddOns, licenseCharges, erp, salesChannels, courierPartners.",
        "synonyms": "license, licensing, software license, subscription, plan, quotas, limits, allowed warehouses, allowed staff, monthly orders, contract, agreement, ijazat nama, license quota",
        "rules": "CRITICAL: Schema is 'ls'. Column configuration has data type TEXT (not jsonb)! AI MUST ALWAYS cast it before extracting fields: CAST(lic.configuration AS json) or lic.configuration::json. Example extraction: (lic.configuration::json ->> 'noOfWarehouseAllowed')::int. Quota vs live usage: compare allowed warehouses with (SELECT COUNT(*) FROM public.location WHERE \"isActive\" = true).",
        "join_hints": [
            "JOIN ls.invoice inv ON (inv.\"billedLicense\"->>'id')::int = license.id -- Invoices for license"
        ]
    },
    "invoice": {
        "service": SERVICE_LS,
        "description": "Stores subscription licensing billing invoices and payment tracking for software tenant subscription fees.",
        "concepts": "id = invoice ID, invoiceNo = invoice reference number (e.g. 'INV-1001'), status = payment enum (PAID, PENDING, DRAFT, EXPIRED), billedLicense = JSONB billed modules breakdown.",
        "synonyms": "invoice, invoices, bill, billing, subscription bill, license invoice, fee, charges, raseed, chalan, payment receipt",
        "rules": "CRITICAL: Schema is 'ls'. Qualify as ls.invoice. Wrap \"invoiceNo\" and \"billedLicense\" in quotes. Paid invoices filter: WHERE ls.invoice.status::text = 'PAID'.",
        "join_hints": []
    },
    "service_providers": {
        "service": SERVICE_LS,
        "description": "Stores third-party SaaS service providers and tenant external integration credentials.",
        "concepts": "id = provider ID, configuration = TEXT settings.",
        "synonyms": "service providers, providers, third party integration, external vendors",
        "rules": "Schema is 'ls'.",
        "join_hints": []
    }
}

# ==============================================================================
# 3. CROSS-SERVICE LOGICAL FOREIGN KEY RELATIONSHIPS
# Documents joins that cross schema boundaries or lack explicit Postgres FK constraints.
# ==============================================================================
CROSS_SERVICE_RELATIONSHIPS = [
    {
        "from_schema": "us", "from_table": "users", "from_column": "locationId",
        "to_schema": "public", "to_table": "location", "to_column": "id",
        "note": "Connects users/staff to their assigned warehouse or store location"
    },
    {
        "from_schema": "us", "from_table": "users", "from_column": "roleId",
        "to_schema": "us", "to_table": "roles", "to_column": "id",
        "note": "Connects users to their assigned system role"
    },
    {
        "from_schema": "us", "from_table": "role_permissions", "from_column": "role",
        "to_schema": "us", "to_table": "roles", "to_column": "id",
        "note": "Maps roles to permission assignments"
    },
    {
        "from_schema": "us", "from_table": "role_permissions", "from_column": "slug",
        "to_schema": "us", "to_table": "permissions", "to_column": "slug",
        "note": "Maps permission assignment to permission definition"
    },
    {
        "from_schema": "us", "from_table": "widgets", "from_column": "userId",
        "to_schema": "us", "to_table": "users", "to_column": "id",
        "note": "Connects dashboard widgets to the owner user"
    },
    {
        "from_schema": "public", "from_table": "order", "from_column": "warehouse_id",
        "to_schema": "public", "to_table": "location", "to_column": "id",
        "note": "Connects customer order to dispatching warehouse location"
    },
    {
        "from_schema": "public", "from_table": "order", "from_column": "courierId",
        "to_schema": "public", "to_table": "courier", "to_column": "id",
        "note": "Connects customer order to shipping courier service"
    },
    {
        "from_schema": "public", "from_table": "order", "from_column": "courierPersonId",
        "to_schema": "public", "to_table": "courier_person", "to_column": "id",
        "note": "Connects customer order to individual delivery rider"
    },
    {
        "from_schema": "public", "from_table": "order", "from_column": "channelId",
        "to_schema": "public", "to_table": "channel", "to_column": "id",
        "note": "Connects customer order to originating storefront channel (Shopify/WooCommerce)"
    },
    {
        "from_schema": "ls", "from_table": "invoice", "from_column": "billedLicense",
        "to_schema": "ls", "to_table": "license", "to_column": "id",
        "note": "Connects billing invoice to subscription license"
    }
]

# ==============================================================================
# 4. COMPREHENSIVE ARCHITECTURE & BUSINESS RULES PROMPT
# Guides the AI Agent on business workflows, Roman Urdu queries, and strict SQL rules.
# ==============================================================================
MARKAZI_ARCHITECTURE_PROMPT = """
# Markazi Unified Multi-Service Architecture & Business Workflows:

The system consists of 3 integrated database services accessible simultaneously in PostgreSQL:

1. Inventory & Operations Hub (IS - Schema 'public'):
   - Master Product Catalog: product (master header) -> product_variant (sellable SKU) -> product_price -> price_list
   - Real-time Inventory: location (warehouse/store) + product_variant -> stock (onHand, reserved, available)
   - Sales & Fulfillment: "order" -> order_item -> product_variant -> stock
   - Logistics & Dispatch: "order" -> courier (DHL, blueex) -> courier_person (rider)
   - Origin Channels: "order" -> channel (SHOPIFY, WOOCOMMERCE) -> partner
   - Lifecycle Audit Trail: "order" -> order_activity (timestamped history of CONFIRMED, PACKING, PACKED, DISPATCHED, DELIVERED, CANCELLED)
   - Accounting & Ledgers: company -> journal -> payment_settings

2. User & Access Management Service (US - Schema 'us'):
   - Users & Staff: us.users (name, email, staffId, cellNo, gender, locationId, roleId, isActive)
   - Access Control (RBAC): us.roles -> us.role_permissions -> us.permissions
   - User Customization: us.widgets (dashboard metric cards) & us.theme_settings (branding)

3. License & Billing Service (LS - Schema 'ls'):
   - Licensing & Quotas: ls.license (configuration text JSON: warehouse limit, staff limit, order quota, ERP, channel/courier addons)
   - Billing & Invoices: ls.invoice (invoiceNo, status: PAID/PENDING/DRAFT/EXPIRED, billedLicense)
   - Service Providers: ls.service_providers

--------------------------------------------------------------------------------
# Critical Inter-Database / Cross-Service Relationships:

1. Staff / User -> Physical Warehouse Assignment (US <-> IS):
   - us.users."locationId" = public.location.id
   - Connects each employee or warehouse operator to their stationed facility branch!
   - Example JOIN:
     SELECT u.name, u.email, u."staffId", l.name AS warehouse_name
     FROM us.users u
     JOIN public.location l ON u."locationId" = l.id
     WHERE u."isActive" = true;

2. Order -> Warehouse & Courier & Channel (IS internal):
   - public."order"."warehouse_id" = public.location.id (fulfillment facility)
   - public."order"."courierId" = public.courier.id (delivery partner: DHL, blueex)
   - public."order"."courierPersonId" = public.courier_person.id (assigned rider)
   - public."order"."channelId" = public.channel.id (Shopify, WooCommerce)

3. Order -> Product Variant -> Master Product (IS internal):
   - public."order" -> order_item."orderId" = "order".id
   - order_item."variantId" = product_variant.id
   - CRITICAL: product_variant."product" can be NULL for standalone SKUs!
     ALWAYS use LEFT JOIN for public.product:
     FROM public."order" AS o
     JOIN public.order_item AS oi ON oi."orderId" = o.id
     JOIN public.product_variant AS pv ON pv.id = oi."variantId"
     LEFT JOIN public.product AS p ON p.id = pv.product;
   - Product name fallback: COALESCE(p.title, pv.title, pv.sku) AS product_name
   - Customer name fallback: COALESCE(o."customerName", o."createdByName") AS customer_name

4. Stock -> Location & Product Variant (IS internal):
   - stock.location = location.id
   - stock.product = product_variant.id
   - Available stock expression: COALESCE(s."available", s."onHand" - s."reserved", 0)

5. Licensing Quotas vs Real Operational Usage (LS <-> IS/US):
   - ls.license.configuration is TEXT (JSON string). ALWAYS cast with ::json or CAST(lic.configuration AS json)!
   - Quota limits:
     * (lic.configuration::json ->> 'noOfWarehouseAllowed')::int AS allowed_warehouses
     * (lic.configuration::json ->> 'noOfStaffAllowed')::int AS allowed_staff
     * (lic.configuration::json ->> 'noOfOrdersProcessingAllowed')::int AS allowed_orders
   - Current actual active counts:
     * Active warehouses: (SELECT COUNT(*) FROM public.location WHERE "isActive" = true)
     * Active staff members: (SELECT COUNT(*) FROM us.users WHERE "isActive" = true)
     * Processed orders: (SELECT COUNT(*) FROM public."order")

--------------------------------------------------------------------------------
# Roman Urdu & English Natural Language Mapping Cheat Sheet:

- "Kitna maal / stock bacha hai" / "inventory kitni hai":
  -> Query public.stock with COALESCE(available, onHand - reserved, 0)
- "Kaun sa mulazim / staff kis warehouse me kaam karta hai":
  -> SELECT u.name, l.name FROM us.users u JOIN public.location l ON u."locationId" = l.id
- "Kamyab delivery / delivered orders":
  -> SELECT * FROM public."order" WHERE "order"."status"::text = 'DELIVERED'
- "Net sales / total revenue / bikri kitni hui":
  -> SELECT SUM("order"."finalAmount") FROM public."order" WHERE "order"."status"::text NOT IN ('CANCELLED', 'RETURNED_BY_CUSTOMER', 'RETURNED_BY_COURIER')
- "Sab se zyada bikne wala saman / top selling items":
  -> SELECT COALESCE(p.title, pv.title, pv.sku), SUM(oi.quantity) AS sold FROM public.order_item oi JOIN public.product_variant pv ON oi."variantId" = pv.id LEFT JOIN public.product p ON pv.product = p.id JOIN public."order" o ON oi."orderId" = o.id WHERE o.status::text NOT IN ('CANCELLED', 'RETURNED_BY_CUSTOMER', 'RETURNED_BY_COURIER') GROUP BY 1 ORDER BY sold DESC
- "License me kitne warehouse / staff allowed hain":
  -> SELECT (configuration::json ->> 'noOfWarehouseAllowed')::int, (configuration::json ->> 'noOfStaffAllowed')::int FROM ls.license
- "Kis courier se kitne parcel gaye":
  -> SELECT c."courierName", COUNT(o.id) FROM public."order" o JOIN public.courier c ON o."courierId" = c.id GROUP BY c."courierName"
- "Kis channel se kitne order aye":
  -> SELECT ch."channelName", COUNT(o.id) FROM public."order" o JOIN public.channel ch ON o."channelId" = ch.id GROUP BY ch."channelName"

--------------------------------------------------------------------------------
# Professional SQL Generation Rules & Edge Cases:

1. SCHEMA SEARCH PATH: The search path is configured as 'public, us, ls'. Always use explicit schema qualification (e.g. us.users, ls.license, public.location, public."order") for total clarity.
2. SENSITIVE IDENTIFIERS & CAMELCASE: Always wrap CamelCase column names and table "order" in double quotes:
   - "order", "orderNo", "channelName", "courierName", "locationId", "roleId", "staffId", "userId", "isActive", "finalAmount", "actualAmount", "shippingFee", "onHand", "totalPrice", "unitPrice", "warehouse_id", "courierId", "channelId", "courierPersonId".
3. ONLY READ-ONLY SELECT: Only SELECT queries are permitted. Never use INSERT, UPDATE, DELETE, or DDL.
4. CASE-INSENSITIVE TEXT FILTERS: Always use ILIKE (e.g. column ILIKE '%term%') for text filtering.
5. ENUM TYPE CASTING: When filtering ENUM columns with ILIKE, cast to text: status::text ILIKE '...'.
6. LOCATION TABLE HAS NO CITY: public.location does NOT have a 'city' column! City is stored in public."order".city. Use location.name or location.address.
7. STANDALONE VARIANTS: product_variant."product" is nullable. Always use LEFT JOIN for public.product.
8. NEVER USE LIMIT UNLESS REQUESTED: Never add LIMIT unless user explicitly asked for top N or first N.
"""


def quote_ident(name: str) -> str:
    """Wraps identifiers in double quotes if they contain uppercase or match SQL keywords."""
    keywords = {"order", "user", "users", "group", "check", "table", "limit", "column", "desc", "asc", "role", "roles", "schema"}
    if name.lower() in keywords or any(c.isupper() for c in name):
        return f'"{name}"'
    return name


class DynamicSchemaCatalogManager:
    def __init__(self):
        self._catalog: dict[str, Any] = {}
        self._dependencies: dict[str, list[str]] = {}
        self._enums: dict[str, str] = {}
        self._is_loaded = False

    def _introspect_enums(self, db_mgr) -> None:
        enums_res = db_mgr._sync_execute("""
            SELECT t.typname, string_agg(e.enumlabel, ', ' ORDER BY e.enumsortorder) as allowed_values
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname IN ('public', 'us', 'ls')
            GROUP BY t.typname;
        """)
        if enums_res.get("success"):
            self._enums = {r["typname"]: r["allowed_values"] for r in enums_res.get("rows", [])}

    def _introspect_table_columns(self, db_mgr, table_entries: list[tuple[str, str]]) -> dict[tuple[str, str], list[tuple]]:
        cols_res = db_mgr._sync_execute("""
            SELECT 
                table_schema, table_name, column_name, data_type, udt_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema IN ('public', 'us', 'ls')
            ORDER BY table_schema, table_name, ordinal_position;
        """)
        table_cols: dict[tuple[str, str], list[tuple]] = {t: [] for t in table_entries}
        for col in cols_res.get("rows", []):
            key = (col["table_schema"], col["table_name"])
            if key not in table_cols:
                continue
            c_name = col["column_name"]
            quoted_c = quote_ident(c_name)
            d_type = col["data_type"]
            udt = col["udt_name"]

            desc_parts = [f"Type: {d_type}"]
            if udt in self._enums:
                desc_parts.append(f"Enum values: {self._enums[udt]}")
                d_type = f"enum ({udt})"

            # Lookup column semantic notes from knowledge base
            col_key = f"{col['table_name']}.{c_name}"
            full_col_key = f"{col['table_schema']}.{col['table_name']}.{c_name}"
            semantic_note = COLUMN_SEMANTIC_NOTES.get(full_col_key) or COLUMN_SEMANTIC_NOTES.get(col_key)
            if semantic_note:
                desc_parts.append(semantic_note)

            desc = " | ".join(desc_parts)
            table_cols[key].append((quoted_c, d_type, desc))
        return table_cols

    def _introspect_relationships(self, db_mgr, table_entries: list[tuple[str, str]]) -> tuple[dict[tuple[str, str], list[str]], dict[str, set[str]], int]:
        fks_res = db_mgr._sync_execute("""
            SELECT 
                tc.table_schema AS from_schema,
                kcu.table_name AS from_table,
                kcu.column_name AS from_column,
                ccu.table_schema AS to_schema,
                ccu.table_name AS to_table,
                ccu.column_name AS to_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema IN ('public', 'us', 'ls');
        """)

        relationships: dict[tuple[str, str], list[str]] = {t: [] for t in table_entries}
        deps: dict[str, set[str]] = {t: set() for _, t in table_entries}

        def add_fk_relation(from_s: str, from_t: str, from_c_raw: str, to_s: str, to_t: str, to_c_raw: str):
            from_key = (from_s, from_t)
            to_key = (to_s, to_t)
            from_c = quote_ident(from_c_raw)
            to_c = quote_ident(to_c_raw)

            from_qual = f"{from_s}.{quote_ident(from_t)}" if from_s != "public" else quote_ident(from_t)
            to_qual = f"{to_s}.{quote_ident(to_t)}" if to_s != "public" else quote_ident(to_t)

            if from_key in relationships:
                join_str = f"JOIN {to_qual} ON {from_qual}.{from_c} = {to_qual}.{to_c}"
                if join_str not in relationships[from_key]:
                    relationships[from_key].append(join_str)
                deps.setdefault(from_t, set()).add(to_t)

            if to_key in relationships:
                rev_join = f"JOIN {from_qual} ON {to_qual}.{to_c} = {from_qual}.{from_c}"
                if rev_join not in relationships[to_key]:
                    relationships[to_key].append(rev_join)
                deps.setdefault(to_t, set()).add(from_t)

        rows = fks_res.get("rows", [])
        for fk in rows:
            add_fk_relation(
                fk["from_schema"], fk["from_table"], fk["from_column"],
                fk["to_schema"], fk["to_table"], fk["to_column"]
            )

        for cs in CROSS_SERVICE_RELATIONSHIPS:
            add_fk_relation(
                cs["from_schema"], cs["from_table"], cs["from_column"],
                cs["to_schema"], cs["to_table"], cs["to_column"]
            )

        return relationships, deps, len(rows)

    def _build_catalog_info(self, table_entries, table_cols, relationships) -> dict[str, Any]:
        new_catalog = {}
        for schema, t_name in table_entries:
            key = (schema, t_name)
            qualified_name = f"{schema}.{quote_ident(t_name)}" if schema != "public" else quote_ident(t_name)
            full_qualified_str = f"{schema}.{quote_ident(t_name)}"

            knowledge = TABLE_PURPOSE_KNOWLEDGE.get(t_name, {})
            service_tag = knowledge.get("service", f"Schema: {schema}")
            desc = knowledge.get("description", f"Table {schema}.{t_name} in Markazi platform.")
            synonyms = knowledge.get("synonyms", t_name)
            rules = knowledge.get("rules", "")
            join_hints = knowledge.get("join_hints", [])

            table_info = {
                "schema": schema,
                "table_name": t_name,
                "service": service_tag,
                "quoted_name": qualified_name,
                "full_name": full_qualified_str,
                "description": f"[{service_tag}] {desc}",
                "synonyms": synonyms,
                "concepts": knowledge.get("concepts", ""),
                "rules": rules,
                "join_hints": join_hints,
                "primary_key": "id",
                "columns": table_cols.get(key, []),
                "relationships": relationships.get(key, [])
            }

            new_catalog[f"{schema}.{t_name}"] = table_info
            if t_name not in new_catalog:
                new_catalog[t_name] = table_info
        return new_catalog

    def load_from_db(self, db_mgr) -> bool:
        """
        Dynamically inspects live PostgreSQL across IS ('public'), US ('us'), and LS ('ls')
        schemas and builds the unified multi-service schema catalog.
        """
        try:
            logger.info("Starting dynamic multi-database schema introspection across public, us, and ls...")
            self._introspect_enums(db_mgr)

            tables_res = db_mgr._sync_execute("""
                SELECT table_schema, table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema IN ('public', 'us', 'ls')
                ORDER BY table_schema, table_name;
            """)
            if not tables_res.get("success") or not tables_res.get("rows"):
                logger.warning("Could not introspect tables from information_schema.")
                return False

            raw_tables = tables_res["rows"]
            table_entries = [(r["table_schema"], r["table_name"]) for r in raw_tables]

            table_cols = self._introspect_table_columns(db_mgr, table_entries)
            relationships, deps, fks_count = self._introspect_relationships(db_mgr, table_entries)

            self._catalog = self._build_catalog_info(table_entries, table_cols, relationships)
            self._dependencies = {t: list(connected) for t, connected in deps.items()}
            self._is_loaded = True
            logger.info(
                f"Dynamic multi-schema introspection complete: {len(table_entries)} tables loaded "
                f"across public, us, and ls ({fks_count} native FKs + {len(CROSS_SERVICE_RELATIONSHIPS)} cross-service links)."
            )
            return True

        except Exception as e:
            logger.error(f"Error during dynamic multi-schema introspection: {e}", exc_info=True)
            return False

    def get_catalog(self) -> dict[str, Any]:
        """Returns the dynamic catalog dictionary."""
        if not self._is_loaded:
            try:
                from app.db import db_manager
                db_manager.initialize()
                self.load_from_db(db_manager)
            except Exception as e:
                logger.warning(f"Could not bootstrap dynamic catalog: {e}")
        return self._catalog

    def get_dependencies(self) -> dict[str, list[str]]:
        """Returns the dynamic foreign key dependency graph."""
        if not self._is_loaded:
            self.get_catalog()
        return self._dependencies

    def get_compact_directory(self) -> str:
        """Returns a compact multi-service catalog directory showing all tables and key columns."""
        catalog = self.get_catalog()
        by_schema: dict[str, list[str]] = {"public": [], "us": [], "ls": []}
        seen = set()
        for t_name, info in catalog.items():
            s = info.get("schema", "public")
            tbl = info.get("table_name", t_name)
            if (s, tbl) in seen:
                continue
            seen.add((s, tbl))
            cols = [c[0].strip('"') for c in info.get("columns", [])[:5]]
            col_preview = ", ".join(cols)
            syn = info.get("synonyms", "").split(",")[0]
            by_schema.setdefault(s, []).append(f"- {s}.{tbl} ({syn}): [{col_preview}...]")

        out = ["# Multi-Service Platform Table Directory:"]
        for s in ("public", "us", "ls"):
            lines = by_schema.get(s, [])
            if lines:
                out.append(f"## Service Schema '{s}':")
                out.extend(lines)
        return "\n".join(out)

    def get_columns_for_table(self, table_name: str) -> list[str]:
        """Returns introspected column names for a given table name dynamically."""
        catalog = self.get_catalog()
        info = catalog.get(table_name)
        if not info:
            for k, v in catalog.items():
                if v.get("table_name") == table_name or k.endswith(f".{table_name}"):
                    info = v
                    break
        if info:
            return [c[0].strip('"') for c in info.get("columns", [])]
        return []

    def get_prompt(self, table_names: list[str]) -> str:
        """Constructs schema prompt dynamically for specified tables, enriched with platform directory and rules."""
        catalog = self.get_catalog()
        parts = []
        seen_tables = set()

        for name in table_names:
            info = catalog.get(name)
            if not info:
                continue
            table_key = f"{info['schema']}.{info['table_name']}"
            if table_key in seen_tables:
                continue
            seen_tables.add(table_key)

            col_lines = [f"    {c[0]}: {c[1]} -- {c[2]}" for c in info.get("columns", [])]
            col_str = "\n".join(col_lines) if col_lines else "    (No columns listed)"
            rel_lines = [f"    -- {r}" for r in info.get("relationships", [])]
            rel_str = "\n".join(rel_lines) if rel_lines else "    -- (No foreign key joins detected)"
            concepts = f"\n  Core Concepts: {info['concepts']}" if info.get('concepts') else ""
            rules = f"\n  Table Rules & Gotchas: {info['rules']}" if info.get('rules') else ""
            join_hints = f"\n  Recommended Join Patterns:\n    " + "\n    ".join(info['join_hints']) if info.get('join_hints') else ""

            parts.append(
                f"TABLE {info['quoted_name']} ({info['description']}):{concepts}{rules}{join_hints}\n"
                f"  Columns:\n{col_str}\n"
                f"  Introspected Joins:\n{rel_str}"
            )

        schema_text = "\n\n".join(parts)
        directory_text = self.get_compact_directory()
        return (
            schema_text + "\n\n" +
            directory_text + "\n\n" +
            MARKAZI_ARCHITECTURE_PROMPT.strip()
        )


catalog_manager = DynamicSchemaCatalogManager()


class _CatalogProxy(dict):
    def __getitem__(self, item):
        return catalog_manager.get_catalog().get(item)

    def __iter__(self):
        return iter(catalog_manager.get_catalog())

    def __len__(self):
        return len(catalog_manager.get_catalog())

    def items(self):
        return catalog_manager.get_catalog().items()

    def keys(self):
        return catalog_manager.get_catalog().keys()

    def values(self):
        return catalog_manager.get_catalog().values()

    def get(self, k, default=None):
        return catalog_manager.get_catalog().get(k, default)

    def __contains__(self, k):
        return k in catalog_manager.get_catalog()


TABLE_CATALOG = _CatalogProxy()


def get_table_schema_prompt(table_names: list[str]) -> str:
    return catalog_manager.get_prompt(table_names)
