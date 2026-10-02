import logging
from typing import Any, Optional

logger = logging.getLogger("markazi.schema")

SERVICE_IS = "IS (Inventory/Operations)"
SERVICE_US = "US (User & Access Management)"
SERVICE_LS = "LS (License & Billing)"

TABLE_PURPOSE_KNOWLEDGE: dict[str, dict[str, str]] = {
    "company": {
        "service": SERVICE_IS,
        "description": "Stores companies/organizations. Supports multiple companies and parent-child hierarchy. Top-level entity for locations, journals, and business data.",
        "concepts": "id = company identifier, title = company name, isActive = status, sourceId = external ID, parentId = parent company",
        "synonyms": "company, companies, brand, organization, merchant, business entity, parent company, child company"
    },
    "company_closure": {
        "service": SERVICE_IS,
        "description": "Stores company hierarchy relationships (ancestor/descendant) for nested parent-child company structures.",
        "concepts": "id_ancestor = parent/ancestor company, id_descendant = child/descendant company",
        "synonyms": "company hierarchy, ancestor, descendant, company tree, parent child relationship"
    },
    "location": {
        "service": SERVICE_IS,
        "description": "Stores warehouses, physical stores, and fulfillment locations where inventory is stored. Connects to companies, stock, and staff users.",
        "concepts": "Location name, type, address, latitude/longitude, company, parent location, warehouseSourceId, isActive, isConfigured",
        "synonyms": "warehouse, godown, store, location, depot, branch, fulfillment center, address, city, physical location, dukan"
    },
    "product": {
        "service": SERVICE_IS,
        "description": "Stores master product records representing general products (e.g. Nike Shoes). Actual SKUs/variants are in product_variant.",
        "concepts": "Master product, title, sourceId. General product definition.",
        "synonyms": "product, master product, products, items, catalog, saman, cheez, parent product"
    },
    "product_variant": {
        "service": SERVICE_IS,
        "description": "Stores individual sellable variants/SKUs (e.g. Nike Shoes Black Size 42) with SKU, barcode, images, and prices.",
        "concepts": "Actual sellable SKU, title, sku, barCode, imageKey, sourceId, product FK.",
        "synonyms": "product variant, SKU, barcode, size, color, variations, sellable item, variant specs, variant title"
    },
    "price_list": {
        "service": SERVICE_IS,
        "description": "Stores pricing catalogs (Retail, Wholesale, Distributor) allowing multiple pricing systems.",
        "concepts": "title, sourceId. Defines rate tiers e.g. Retail Price, Wholesale Price.",
        "synonyms": "price list, rate list, wholesale price, retail price, price tiers, distributor price"
    },
    "product_price": {
        "service": SERVICE_IS,
        "description": "Connects product variants with price lists and stores their prices (product_variant -> product_price <- price_list).",
        "concepts": "price, productVariant FK, priceList FK.",
        "synonyms": "product price, selling price, rate, qeemat, keemat, cost, price entry, item rate"
    },
    "stock": {
        "service": SERVICE_IS,
        "description": "Stores inventory quantities for product variants at locations. Tracks physical onHand, reserved for orders, and available stock.",
        "concepts": "product = product_variant FK, location = location FK, onHand = physical stock, reserved = reserved for orders, available = stock available for new orders",
        "synonyms": "stock, inventory, onHand, reserved, available, warehouse stock, godown maal, bacha hua maal, quantities, balance, kitna saman bacha"
    },
    "order": {
        "service": SERVICE_IS,
        "description": "Main customer order table. Stores complete sales, customer details, financial amounts (actual, discount, shipping, final), and statuses.",
        "concepts": "orderNo, customerName, phone, email, address, city, actualAmount, discount, shippingFee, finalAmount, status, courier, warehouse, channel",
        "synonyms": "order, sales, orders, customer order, consignment, booking, status, bikri, khareed, customer details, revenue, turnover"
    },
    "order_item": {
        "service": SERVICE_IS,
        "description": "Stores products inside an order (line items). Connects order with product_variant with quantity, unitPrice, totalPrice, discounts.",
        "concepts": "orderId, variantId, quantity, unitPrice, totalPrice, discountAmount, itemState, isScanned",
        "synonyms": "order item, order items, line items, ordered quantity, unitPrice, totalPrice, item details, items per order"
    },
    "order_activity": {
        "service": SERVICE_IS,
        "description": "Stores the history/timeline and audit trail of order status events (CONFIRMED, PACKING, PACKED, DISPATCHED, DELIVERED, CANCELLED, RETURNED).",
        "concepts": "orderId, status, activityAt, performed by user. Full historical event trail vs order.status current status.",
        "synonyms": "order activity, order timeline, order history, status updates, audit trail, lifecycle events"
    },
    "courier": {
        "service": SERVICE_IS,
        "description": "Stores courier and delivery services (TCS, Leopards, Trax) used by orders for shipping.",
        "concepts": "courierName, configuration, partnerId.",
        "synonyms": "courier, shipping partner, delivery company, TCS, Leopards, Trax, Call Courier, logistics provider"
    },
    "courier_person": {
        "service": SERVICE_IS,
        "description": "Stores individual courier delivery riders/persons associated with order delivery.",
        "concepts": "name, document URL, courier-related identification.",
        "synonyms": "courier person, rider, delivery boy, dispatch rider, courier driver"
    },
    "channel": {
        "service": SERVICE_IS,
        "description": "Stores sales and order channels (Shopify, WooCommerce, Amazon, Daraz, etc.) where orders originate.",
        "concepts": "channelName, configuration, partnerId, isAddon.",
        "synonyms": "channel, sales channel, shopify, woocommerce, daraz, online store, marketplace, order source"
    },
    "partner": {
        "service": SERVICE_IS,
        "description": "Stores external integration and business partners associated with sales channels and couriers.",
        "concepts": "name, configuration, partner integrations.",
        "synonyms": "partner, vendor, supplier, external affiliate, integration partner"
    },
    "erp": {
        "service": SERVICE_IS,
        "description": "Stores connected ERP integration configurations, ERP names, and connection status.",
        "concepts": "ERP name, configuration, connection status.",
        "synonyms": "erp, erp integration, external erp, accounting system connection"
    },
    "journal": {
        "service": SERVICE_IS,
        "description": "Stores accounting and financial journals associated with companies.",
        "concepts": "journal name, journal code, journal type, company FK.",
        "synonyms": "journal, accounting journal, general ledger, financial ledger, accounts"
    },
    "payment_settings": {
        "service": SERVICE_IS,
        "description": "Stores payment and accounting configuration connecting payment modes with accounting journals.",
        "concepts": "name, direction, account ID, source ID, journal FK.",
        "synonyms": "payment settings, payment configuration, account mappings, payment gateway settings"
    },
    "notification": {
        "service": SERVICE_IS,
        "description": "Stores system notifications for users and order lifecycle events (CONFIRMED, PACKED, DELIVERED, CANCELLED, etc.).",
        "concepts": "title, message, type (enum), receiver, read/unread, createdAt.",
        "synonyms": "notification, system notification, alert, message, event notification"
    },
    "settings": {
        "service": SERVICE_IS,
        "description": "Stores global application and system configuration (duplicate order rules, courier rules, warehouse defaults). Technical config, not transactional business data.",
        "concepts": "configuration data, duplicate orders, courier settings, warehouse settings.",
        "synonyms": "settings, system settings, app configuration, preferences"
    },
    "system_log": {
        "service": SERVICE_IS,
        "description": "Stores system/API request and response logs for debugging, monitoring, and auditing. Do NOT treat as normal business data.",
        "concepts": "source, requestUrl, requestBody, response, created_at.",
        "synonyms": "system log, api log, request log, audit log, debug logs"
    },
    "migration_table": {
        "service": "Technical",
        "description": "Tracks executed database migrations. Technical database maintenance table, NOT for business reporting.",
        "concepts": "migration tracking, schema versions.",
        "synonyms": "migrations, database migrations, schema history"
    },

    "users": {
        "service": SERVICE_US,
        "description": "User Service: Stores system users, employees, admins, operators, and staff accounts. Connects to roles for access control and location for warehouse/store branch assignment.",
        "concepts": "id = user ID, name = full name, email = login email, staffId = staff identifier, roleId = FK to roles.id, locationId = FK to location.id (assigned warehouse/store), isActive = active status, isPlatformAdmin = platform admin flag, isVendorAdmin = vendor admin flag, cellNo = contact number, gender = gender enum",
        "synonyms": "users, user, employee, staff, admin, operator, account, mulazim, bande, team member, profile, workers"
    },
    "roles": {
        "service": SERVICE_US,
        "description": "User Service: Stores user roles and permission designations (e.g. Staff Admin, Manager, Warehouse Operator).",
        "concepts": "id = role ID, title = role title/designation, description = role description, isActive = active flag",
        "synonyms": "roles, role, user role, designation, job title, position, access level, uhda, permissions role"
    },
    "permissions": {
        "service": SERVICE_US,
        "description": "User Service: Stores granular system privileges and permission definitions categorized by module.",
        "concepts": "id = permission ID, module = functional module name, permission = permission title, slug = unique permission identifier, description = details",
        "synonyms": "permissions, permission, privileges, access rights, feature rights, module rights, permission slug"
    },
    "role_permissions": {
        "service": SERVICE_US,
        "description": "User Service: Junction table mapping roles to their assigned permission slugs (roles <-> permissions).",
        "concepts": "id = mapping ID, role = FK to roles.id, slug = FK to permissions.slug",
        "synonyms": "role permissions, role permission, assigned permissions, access mapping, role rights"
    },
    "widgets": {
        "service": SERVICE_US,
        "description": "User Service: Stores user-customized dashboard widgets, metric cards, layouts, and position coordinates.",
        "concepts": "id = widget ID, userId = FK to users.id, title = widget title, description, key = metric identifier, icon = icon name, xAxis/yAxis/height/width = grid dimensions",
        "synonyms": "widgets, widget, dashboard widget, dashboard card, metrics card, user layout, analytics card"
    },
    "theme_settings": {
        "service": SERVICE_US,
        "description": "User Service: Stores UI visual theme, branding configuration, custom logo URL, and brand color palette.",
        "concepts": "logo = logo URL, brandColorsSettings = JSONB color scheme",
        "synonyms": "theme settings, theme, branding, brand colors, logo, ui settings, appearance"
    },

    "license": {
        "service": SERVICE_LS,
        "description": "License Service: Stores tenant software licenses, permitted feature quotas (warehouses, staff, orders), channels, couriers, and ERP configurations.",
        "concepts": "id = license ID, configuration = JSON specification containing allowed warehouses (noOfWarehouseAllowed), staff limit (noOfStaffAllowed), monthly order quotas (noOfOrdersProcessingAllowed), configured salesChannels, courierPartners, and ERP integrations",
        "synonyms": "license, licensing, software license, subscription, plan, quotas, limits, allowed warehouses, allowed staff, contract, agreement"
    },
    "invoice": {
        "service": SERVICE_LS,
        "description": "License Service: Stores software subscription and licensing billing invoices, payment statuses, and billed license breakdowns.",
        "concepts": "id = invoice ID, invoiceNo = invoice reference number, status = invoice status enum (PAID, PENDING, OVERDUE), billedLicense = JSONB billed breakdown",
        "synonyms": "invoice, invoices, bill, billing, subscription bill, license invoice, fee, charges, raseed, chalan"
    },
    "service_providers": {
        "service": SERVICE_LS,
        "description": "License Service: Stores service provider integration settings and third-party configuration parameters.",
        "concepts": "id = provider ID, configuration = JSON connection and capability parameters",
        "synonyms": "service providers, providers, integrations, third party provider, external services"
    }
}

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
        "from_schema": "ls", "from_table": "invoice", "from_column": "billedLicense",
        "to_schema": "ls", "to_table": "license", "to_column": "id",
        "note": "Connects billing invoice to subscription license"
    }
]

MARKAZI_ARCHITECTURE_PROMPT = """
# Markazi Unified Multi-Database / Multi-Service Architecture & Business Flows:

The system consists of 3 integrated databases unified seamlessly via PostgreSQL Foreign Data Wrappers (FDW):

1. Inventory & Operations Hub (IS - Schema 'public'):
   - Master Catalog: PRODUCT -> PRODUCT_VARIANT -> PRODUCT_PRICE -> PRICE_LIST
   - Inventory: LOCATION (Warehouse/Store) + PRODUCT_VARIANT -> STOCK (onHand, reserved, available)
   - Sales & Fulfillment: CUSTOMER -> "order" -> ORDER_ITEM -> PRODUCT_VARIANT -> STOCK
   - Logistics: "order" -> COURIER -> COURIER_PERSON
   - Channels: "order" -> CHANNEL -> PARTNER
   - Lifecycle Audit: "order" -> ORDER_ACTIVITY -> NOTIFICATION
   - Accounting: COMPANY -> JOURNAL -> PAYMENT_SETTINGS

2. User & Access Management Service (US - Schema 'us'):
   - Users & Staff: USERS (name, email, staffId, cellNo, locationId, roleId, isActive)
   - Access Control: ROLES -> ROLE_PERMISSIONS -> PERMISSIONS
   - User Customization: USERS -> WIDGETS (Dashboard cards) & THEME_SETTINGS

3. License & Billing Service (LS - Schema 'ls'):
   - Licensing & Quotas: LICENSE (configuration: warehouse limit, staff limit, order quota, ERP, channel/courier add-ons)
   - Billing: INVOICE (invoiceNo, status, billedLicense)
   - Integrations: SERVICE_PROVIDERS

# Critical Inter-Database / Cross-Service Relationships:
1. User -> Warehouse/Location (US <-> IS):
   - us.users."locationId" = public.location.id
   - Connects users/employees/operators to their assigned physical warehouse or store location!
   - Example JOIN: FROM us.users u JOIN public.location l ON u."locationId" = l.id
2. User -> Roles & Access (US internal):
   - us.users."roleId" = us.roles.id
   - us.role_permissions.role = us.roles.id
   - us.role_permissions.slug = us.permissions.slug
   - Example JOIN: FROM us.users u LEFT JOIN us.roles r ON u."roleId" = r.id
3. User -> Dashboard Widgets (US internal):
   - us.widgets."userId" = us.users.id
4. Order -> Product Variant -> Master Product (IS internal):
   - "order" -> order_item."orderId" = "order".id
   - order_item."variantId" = product_variant.id
   - CRITICAL: product_variant."product" can be NULL for standalone variants!
     ALWAYS use LEFT JOIN for public.product:
     FROM public."order" AS o
     JOIN public.order_item AS oi ON oi."orderId" = o.id
     JOIN public.product_variant AS pv ON pv.id = oi."variantId"
     LEFT JOIN public.product AS p ON p.id = pv.product
   - Product name: COALESCE(p.title, pv.title, pv.sku) AS product_name
   - Customer name who ordered: COALESCE(o."customerName", o."createdByName") AS customer_name
5. Stock -> Location & Product Variant (IS internal):
   - stock.location = location.id
   - stock.product = product_variant.id
   - Product Variant: product_variant.product is nullable. Always use LEFT JOIN public.product p ON p.id = pv.product.
   - Available stock expression: COALESCE(s."available", s."onHand" - s."reserved", 0)
6. Licensing -> Operational Quotas (LS <-> IS/US):
   - ls.license.configuration contains JSON limits (e.g. noOfWarehouseAllowed, noOfStaffAllowed, noOfOrdersProcessingAllowed).
   - CRITICAL: ls.license.configuration is of data type TEXT (not jsonb). ALWAYS cast with CAST(lic.configuration AS json) or lic.configuration::json!
     Example: CAST(lic.configuration AS json) ->> 'noOfWarehouseAllowed'
     Numeric casting: (CAST(lic.configuration AS json) ->> 'noOfWarehouseAllowed')::int
   - Active warehouses count: (SELECT COUNT(*) FROM public.location WHERE "isActive" = true)
   - Active users count: (SELECT COUNT(*) FROM us.users WHERE "isActive" = true)

# Professional SQL Generation Rules:
1. SCHEMA SEARCH PATH: The search path is configured as 'public, us, ls'. You may qualify table names explicitly (e.g. us.users, ls.license, public."order") or use short table names (users, roles, license, "order"). Explicit schema qualification is recommended for clarity.
2. SENSITIVE IDENTIFIERS: Always wrap CamelCase or reserved keywords in double quotes:
   - "order", "orderNo", "channelName", "locationId", "roleId", "staffId", "userId", "isActive", "finalAmount", "onHand", "totalPrice".
3. ONLY READ-ONLY SELECT: Only SELECT queries are permitted. Never use INSERT, UPDATE, DELETE, or DDL.
4. INVENTORY LOGIC: Available stock calculation:
   COALESCE(stock."available", stock."onHand" - stock."reserved", 0)
5. NET REVENUE / SALES LOGIC: When calculating net sales or order counts, ALWAYS exclude cancelled and returned orders:
   WHERE "order"."status"::text NOT IN ('CANCELLED', 'RETURNED_BY_CUSTOMER', 'RETURNED_BY_COURIER')
6. USERS & STAFF QUERIES:
   - For user profiles, employees, or staff: query us.users (or users).
   - If user asks which staff/user belongs to which warehouse/location: JOIN us.users with public.location ON us.users."locationId" = public.location.id.
   - For user designations/roles: JOIN us.users with us.roles ON us.users."roleId" = us.roles.id.
7. LICENSE & QUOTA QUERIES:
   - For licensing details, allowed limits, or ERP/channel integrations: query ls.license.
   - Remember ls.license.configuration is TEXT: ALWAYS use CAST(configuration AS json) ->> 'noOfWarehouseAllowed' or ::json.
   - For invoices or subscription billing status: query ls.invoice.
8. LOCATION / WAREHOUSE COLUMNS:
   - public.location has: id, name, address, type, "isActive", "isConfigured", latitude, longitude, "parentId", "companyId".
   - CRITICAL: public.location does NOT have a 'city' column! (City is only in public."order"). Use location.name or location.address.
9. EXCLUDED TECHNICAL TABLES: Do not query 'system_log' or 'migration_table' unless specifically requested by user.
10. NEVER INVENT COLUMNS: Use strictly the introspected columns shown in the schema context.
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
            
            desc = f"Type: {d_type}"
            if udt in self._enums:
                desc = f"Enum values: {self._enums[udt]}"
                d_type = f"enum ({udt})"

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

            table_info = {
                "schema": schema,
                "table_name": t_name,
                "service": service_tag,
                "quoted_name": qualified_name,
                "full_name": full_qualified_str,
                "description": f"[{service_tag}] {desc}",
                "synonyms": synonyms,
                "concepts": knowledge.get("concepts", ""),
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

            parts.append(
                f"TABLE {info['quoted_name']} ({info['description']}):{concepts}\n"
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
