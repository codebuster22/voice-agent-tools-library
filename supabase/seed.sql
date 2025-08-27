-- Automotive Inventory Test Data
-- This file contains comprehensive test data for the car dealership voice agent system

-- Insert sample vehicles (12 vehicles across 4 categories)
INSERT INTO vehicles (id, brand, model, year, category, base_price, image_url, is_active, created_at, updated_at) VALUES
-- Sedans
('550e8400-e29b-41d4-a716-446655440001', 'Toyota', 'Camry', 2024, 'sedan', 2500000, 'https://example.com/images/camry.jpg', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440002', 'Honda', 'Accord', 2024, 'sedan', 2700000, 'https://example.com/images/accord.jpg', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440003', 'BMW', '3 Series', 2024, 'sedan', 4500000, 'https://example.com/images/bmw3.jpg', true, NOW(), NOW()),

-- SUVs
('550e8400-e29b-41d4-a716-446655440004', 'Toyota', 'RAV4', 2024, 'suv', 3200000, 'https://example.com/images/rav4.jpg', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440005', 'Honda', 'CR-V', 2024, 'suv', 3400000, 'https://example.com/images/crv.jpg', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440006', 'Ford', 'Explorer', 2024, 'suv', 3800000, 'https://example.com/images/explorer.jpg', true, NOW(), NOW()),

-- Trucks
('550e8400-e29b-41d4-a716-446655440007', 'Ford', 'F-150', 2024, 'truck', 4200000, 'https://example.com/images/f150.jpg', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440008', 'Chevrolet', 'Silverado', 2024, 'truck', 4000000, 'https://example.com/images/silverado.jpg', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440009', 'Toyota', 'Tacoma', 2023, 'truck', 3700000, 'https://example.com/images/tacoma.jpg', true, NOW(), NOW()),

-- Coupes
('550e8400-e29b-41d4-a716-44665544000a', 'BMW', 'M4', 2024, 'coupe', 7500000, 'https://example.com/images/m4.jpg', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-44665544000b', 'Ford', 'Mustang GT', 2024, 'coupe', 4800000, 'https://example.com/images/mustang.jpg', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-44665544000c', 'Tesla', 'Model S', 2024, 'sedan', 8000000, 'https://example.com/images/models.jpg', true, NOW(), NOW());

-- Insert inventory items (25 records with realistic variety)
INSERT INTO inventory (id, vehicle_id, vin, color, features, status, location, current_price, expected_delivery_date, created_at, updated_at) VALUES
-- Toyota Camry inventory
('650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', '1HGCM82633A123456', 'Silver', '["Bluetooth", "Backup Camera", "Automatic Climate Control"]', 'available', 'main_dealership', 2500000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', '1HGCM82633A123457', 'White', '["Leather Seats", "Sunroof", "Navigation System", "Heated Seats"]', 'available', 'main_dealership', 2800000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', '1HGCM82633A123458', 'Red', '["Sport Package", "Premium Audio", "Alloy Wheels"]', 'reserved', 'main_dealership', 2700000, '2025-09-01', NOW(), NOW()),

-- Honda Accord inventory  
('650e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', '1HGCM82633A123459', 'Black', '["Honda Sensing Suite", "Wireless Charging", "Premium Audio"]', 'available', 'main_dealership', 2700000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', '1HGCM82633A123460', 'Blue', '["Leather Seats", "Navigation System", "Heated Seats", "Sunroof"]', 'available', 'north_branch', 2950000, NULL, NOW(), NOW()),

-- BMW 3 Series inventory
('650e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440003', '1HGCM82633A123461', 'White', '["Premium Package", "Driver Assistance Package", "Harman Kardon Audio"]', 'available', 'main_dealership', 4800000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440003', '1HGCM82633A123462', 'Black', '["M Sport Package", "Premium Package", "Adaptive Suspension"]', 'sold', 'main_dealership', 5200000, NULL, NOW(), NOW()),

-- Toyota RAV4 inventory
('650e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440004', '1HGCM82633A123463', 'Silver', '["All-Wheel Drive", "Safety Sense 2.0", "Power Liftgate"]', 'available', 'main_dealership', 3200000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440004', '1HGCM82633A123464', 'Red', '["All-Wheel Drive", "Premium Audio", "Roof Rails", "Heated Seats"]', 'available', 'service_center', 3500000, NULL, NOW(), NOW()),

-- Honda CR-V inventory
('650e8400-e29b-41d4-a716-44665544000a', '550e8400-e29b-41d4-a716-446655440005', '1HGCM82633A123465', 'White', '["All-Wheel Drive", "Honda Sensing Suite", "Power Tailgate"]', 'available', 'main_dealership', 3400000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-44665544000b', '550e8400-e29b-41d4-a716-446655440005', '1HGCM82633A123466', 'Gray', '["All-Wheel Drive", "Leather Seats", "Navigation System", "Premium Audio"]', 'reserved', 'main_dealership', 3750000, '2025-09-15', NOW(), NOW()),

-- Ford Explorer inventory
('650e8400-e29b-41d4-a716-44665544000c', '550e8400-e29b-41d4-a716-446655440006', '1HGCM82633A123467', 'Blue', '["4WD", "Third Row Seating", "SYNC 4A", "Co-Pilot360"]', 'available', 'main_dealership', 3800000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-44665544000d', '550e8400-e29b-41d4-a716-446655440006', '1HGCM82633A123468', 'Black', '["4WD", "Premium Package", "Panoramic Roof", "B&O Audio"]', 'available', 'north_branch', 4200000, NULL, NOW(), NOW()),

-- Ford F-150 inventory
('650e8400-e29b-41d4-a716-44665544000e', '550e8400-e29b-41d4-a716-446655440007', '1HGCM82633A123469', 'White', '["4WD", "Crew Cab", "Bed Liner", "Towing Package"]', 'available', 'main_dealership', 4200000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-44665544000f', '550e8400-e29b-41d4-a716-446655440007', '1HGCM82633A123470', 'Red', '["4WD", "Lariat Package", "Navigation", "Premium Audio", "Leather Seats"]', 'available', 'main_dealership', 4800000, NULL, NOW(), NOW()),

-- Chevrolet Silverado inventory
('650e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440008', '1HGCM82633A123471', 'Silver', '["4WD", "Crew Cab", "Chevy Safety Assist", "Bed Protection"]', 'available', 'service_center', 4000000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440011', '550e8400-e29b-41d4-a716-446655440008', '1HGCM82633A123472', 'Black', '["4WD", "LTZ Package", "Premium Audio", "Heated/Cooled Seats"]', 'reserved', 'main_dealership', 4500000, '2025-08-30', NOW(), NOW()),

-- Toyota Tacoma inventory
('650e8400-e29b-41d4-a716-446655440012', '550e8400-e29b-41d4-a716-446655440009', '1HGCM82633A123473', 'Gray', '["4WD", "TRD Off-Road Package", "Premium Audio"]', 'available', 'main_dealership', 3700000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440013', '550e8400-e29b-41d4-a716-446655440009', '1HGCM82633A123474', 'White', '["4WD", "TRD Pro Package", "Navigation System", "JBL Audio"]', 'available', 'north_branch', 4100000, NULL, NOW(), NOW()),

-- BMW M4 inventory
('650e8400-e29b-41d4-a716-446655440014', '550e8400-e29b-41d4-a716-44665544000a', '1HGCM82633A123475', 'Blue', '["Competition Package", "Carbon Fiber Roof", "Premium Package"]', 'available', 'main_dealership', 7800000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440015', '550e8400-e29b-41d4-a716-44665544000a', '1HGCM82633A123476', 'White', '["Competition Package", "Track Package", "Ceramic Brakes"]', 'reserved', 'main_dealership', 8500000, '2025-09-20', NOW(), NOW()),

-- Ford Mustang GT inventory
('650e8400-e29b-41d4-a716-446655440016', '550e8400-e29b-41d4-a716-44665544000b', '1HGCM82633A123477', 'Red', '["Performance Package", "Premium Audio", "Navigation System"]', 'available', 'main_dealership', 4800000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440017', '550e8400-e29b-41d4-a716-44665544000b', '1HGCM82633A123478', 'Black', '["Performance Package", "Recaro Seats", "Track Apps"]', 'available', 'service_center', 5200000, NULL, NOW(), NOW()),

-- Tesla Model S inventory
('650e8400-e29b-41d4-a716-446655440018', '550e8400-e29b-41d4-a716-44665544000c', '1HGCM82633A123479', 'White', '["Autopilot", "Premium Interior", "Glass Roof", "Enhanced Audio"]', 'available', 'main_dealership', 8000000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-446655440019', '550e8400-e29b-41d4-a716-44665544000c', '1HGCM82633A123480', 'Black', '["Full Self-Driving", "Premium Interior", "Performance Upgrade"]', 'reserved', 'main_dealership', 9500000, '2025-09-10', NOW(), NOW()),

-- Additional mixed inventory for variety
('650e8400-e29b-41d4-a716-44665544001a', '550e8400-e29b-41d4-a716-446655440001', '1HGCM82633A123481', 'Blue', '["Base Model", "Bluetooth", "Backup Camera"]', 'sold', 'main_dealership', 2450000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-44665544001b', '550e8400-e29b-41d4-a716-446655440004', '1HGCM82633A123482', 'Green', '["All-Wheel Drive", "Premium Package", "Roof Rails"]', 'available', 'north_branch', 3600000, NULL, NOW(), NOW()),
('650e8400-e29b-41d4-a716-44665544001c', '550e8400-e29b-41d4-a716-446655440007', '1HGCM82633A123483', 'Gray', '["4WD", "Work Truck Package", "Heavy Duty Towing"]', 'available', 'service_center', 4500000, '2025-09-05', NOW(), NOW());

-- Insert pricing information (current pricing for all vehicles)
INSERT INTO pricing (id, vehicle_id, base_price, feature_prices, discount_amount, is_current, effective_date, created_at) VALUES
-- Toyota Camry pricing
('750e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 2500000, '{"Leather Seats": 150000, "Sunroof": 120000, "Navigation System": 180000, "Heated Seats": 80000, "Premium Audio": 100000, "Sport Package": 200000, "Alloy Wheels": 120000}', 0, true, '2025-08-01', NOW()),

-- Honda Accord pricing
('750e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 2700000, '{"Honda Sensing Suite": 150000, "Wireless Charging": 50000, "Premium Audio": 100000, "Leather Seats": 150000, "Navigation System": 180000, "Heated Seats": 80000, "Sunroof": 120000}', 50000, true, '2025-08-01', NOW()),

-- BMW 3 Series pricing
('750e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 4500000, '{"Premium Package": 300000, "Driver Assistance Package": 200000, "Harman Kardon Audio": 150000, "M Sport Package": 400000, "Adaptive Suspension": 250000}', 200000, true, '2025-08-01', NOW()),

-- Toyota RAV4 pricing
('750e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440004', 3200000, '{"All-Wheel Drive": 150000, "Safety Sense 2.0": 100000, "Power Liftgate": 80000, "Premium Audio": 100000, "Roof Rails": 60000, "Heated Seats": 80000}', 0, true, '2025-08-01', NOW()),

-- Honda CR-V pricing
('750e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440005', 3400000, '{"All-Wheel Drive": 150000, "Honda Sensing Suite": 150000, "Power Tailgate": 80000, "Leather Seats": 150000, "Navigation System": 180000, "Premium Audio": 100000}', 0, true, '2025-08-01', NOW()),

-- Ford Explorer pricing
('750e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440006', 3800000, '{"4WD": 200000, "Third Row Seating": 150000, "SYNC 4A": 120000, "Co-Pilot360": 180000, "Premium Package": 300000, "Panoramic Roof": 150000, "B&O Audio": 200000}', 100000, true, '2025-08-01', NOW()),

-- Ford F-150 pricing
('750e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440007', 4200000, '{"4WD": 250000, "Crew Cab": 200000, "Bed Liner": 80000, "Towing Package": 150000, "Lariat Package": 400000, "Navigation": 180000, "Premium Audio": 120000, "Leather Seats": 150000}', 0, true, '2025-08-01', NOW()),

-- Chevrolet Silverado pricing
('750e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440008', 4000000, '{"4WD": 250000, "Crew Cab": 200000, "Chevy Safety Assist": 120000, "Bed Protection": 100000, "LTZ Package": 350000, "Premium Audio": 120000, "Heated/Cooled Seats": 200000}', 150000, true, '2025-08-01', NOW()),

-- Toyota Tacoma pricing
('750e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440009', 3700000, '{"4WD": 200000, "TRD Off-Road Package": 300000, "Premium Audio": 100000, "TRD Pro Package": 500000, "Navigation System": 180000, "JBL Audio": 150000}', 0, true, '2025-08-01', NOW()),

-- BMW M4 pricing
('750e8400-e29b-41d4-a716-44665544000a', '550e8400-e29b-41d4-a716-44665544000a', 7500000, '{"Competition Package": 800000, "Carbon Fiber Roof": 300000, "Premium Package": 400000, "Track Package": 500000, "Ceramic Brakes": 600000}', 300000, true, '2025-08-01', NOW()),

-- Ford Mustang GT pricing
('750e8400-e29b-41d4-a716-44665544000b', '550e8400-e29b-41d4-a716-44665544000b', 4800000, '{"Performance Package": 400000, "Premium Audio": 120000, "Navigation System": 180000, "Recaro Seats": 250000, "Track Apps": 100000}', 0, true, '2025-08-01', NOW()),

-- Tesla Model S pricing
('750e8400-e29b-41d4-a716-44665544000c', '550e8400-e29b-41d4-a716-44665544000c', 8000000, '{"Autopilot": 800000, "Premium Interior": 200000, "Glass Roof": 150000, "Enhanced Audio": 250000, "Full Self-Driving": 1500000, "Performance Upgrade": 2000000}', 0, true, '2025-08-01', NOW());

-- Add some historical pricing (for testing pricing trends)
INSERT INTO pricing (id, vehicle_id, base_price, feature_prices, discount_amount, is_current, effective_date, created_at) VALUES
-- Historical pricing examples
('750e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440001', 2550000, '{"Leather Seats": 160000, "Sunroof": 130000}', 0, false, '2025-06-01', NOW() - INTERVAL '2 months'),
('750e8400-e29b-41d4-a716-446655440102', '550e8400-e29b-41d4-a716-446655440002', 2750000, '{"Premium Audio": 110000, "Navigation System": 190000}', 0, false, '2025-06-01', NOW() - INTERVAL '2 months'),
('750e8400-e29b-41d4-a716-446655440103', '550e8400-e29b-41d4-a716-446655440003', 4600000, '{"Premium Package": 320000, "M Sport Package": 420000}', 100000, false, '2025-06-01', NOW() - INTERVAL '2 months');