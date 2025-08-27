-- Initial automotive inventory schema
-- Creates tables for vehicles, inventory, and pricing

-- Create vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand VARCHAR NOT NULL,
    model VARCHAR NOT NULL,
    year INTEGER NOT NULL,
    category VARCHAR NOT NULL CHECK (category IN ('sedan', 'suv', 'truck', 'coupe')),
    base_price INTEGER NOT NULL CHECK (base_price > 0),
    image_url VARCHAR,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    vin VARCHAR UNIQUE NOT NULL,
    color VARCHAR NOT NULL,
    features JSONB DEFAULT '[]'::jsonb,
    status VARCHAR DEFAULT 'available' CHECK (status IN ('available', 'sold', 'reserved')),
    location VARCHAR DEFAULT 'main_dealership',
    current_price INTEGER NOT NULL CHECK (current_price > 0),
    expected_delivery_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create pricing table
CREATE TABLE IF NOT EXISTS pricing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    base_price INTEGER NOT NULL CHECK (base_price > 0),
    feature_prices JSONB DEFAULT '{}'::jsonb,
    discount_amount INTEGER DEFAULT 0 CHECK (discount_amount >= 0),
    is_current BOOLEAN DEFAULT true,
    effective_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_vehicles_category ON vehicles(category);
CREATE INDEX IF NOT EXISTS idx_vehicles_brand_model ON vehicles(brand, model);
CREATE INDEX IF NOT EXISTS idx_vehicles_active ON vehicles(is_active);
CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status);
CREATE INDEX IF NOT EXISTS idx_inventory_vehicle_id ON inventory(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_inventory_price ON inventory(current_price);
CREATE INDEX IF NOT EXISTS idx_pricing_current ON pricing(is_current, vehicle_id);
CREATE INDEX IF NOT EXISTS idx_pricing_vehicle_id ON pricing(vehicle_id);