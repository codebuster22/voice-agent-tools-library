# Automotive Voice Agent API Server

Simple, open FastAPI server exposing all 13 automotive dealership tools via HTTP endpoints.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Start the server:**
   ```bash
   uv run python server.py
   ```

3. **Test the server:**
   ```bash
   uv run python test_server.py
   ```

4. **View API documentation:**
   Open http://localhost:8000/docs in your browser

## 📋 Available Endpoints

### Health Check
- `GET /api/v1/health` - Server health status

### Calendar Tools (6 endpoints)
- `POST /api/v1/calendar/list-calendars`
- `POST /api/v1/calendar/get-availability` 
- `POST /api/v1/calendar/get-events`
- `POST /api/v1/calendar/create-event`
- `POST /api/v1/calendar/update-event`
- `POST /api/v1/calendar/delete-event`

### Knowledge Base Tools (2 endpoints)
- `POST /api/v1/knowledge-base/fetch-latest`
- `POST /api/v1/knowledge-base/sync`

### Inventory Tools (5 endpoints)
- `POST /api/v1/inventory/check-inventory`
- `POST /api/v1/inventory/get-delivery-dates`
- `POST /api/v1/inventory/get-prices`
- `POST /api/v1/inventory/get-similar-vehicles`
- `POST /api/v1/inventory/get-vehicle-details`

## 🔧 Example Usage

### Check Available Vehicles
```bash
curl -X POST "http://localhost:8000/api/v1/inventory/check-inventory" \
  -H "Content-Type: application/json" \
  -d '{"category": "sedan", "status": "available", "max_price": 30000}'
```

### List Calendars
```bash
curl -X POST "http://localhost:8000/api/v1/calendar/list-calendars" \
  -H "Content-Type: application/json" \
  -d '{"user_email": "your@email.com", "max_results": 10}'
```

### Get Vehicle Details
```bash
curl -X POST "http://localhost:8000/api/v1/inventory/get-vehicle-details" \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id": "550e8400-e29b-41d4-a716-446655440001", "include_pricing": true}'
```

## 📖 API Documentation

The server automatically generates comprehensive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🏗️ Architecture

### Simple & Clean
- **FastAPI**: Modern, async-first web framework
- **Pydantic**: Request/response validation
- **Direct tool integration**: No complex layers, just HTTP → Tool → Response
- **CORS enabled**: Open access for voice agent integration

### Response Format
All endpoints return consistent JSON responses:
```json
{
  "success": true,
  "message": null,
  "data": { ... },
  "tool_name": "check_inventory",
  "execution_time_ms": 516.59
}
```

### Error Handling
- **400**: Invalid request parameters
- **500**: Tool execution errors
- **401**: Authentication failures (calendar endpoints)

## 🔐 Authentication

- **No authentication required** for MVP
- **Calendar endpoints**: Require `user_email` in request body
- **Inventory/KB endpoints**: No authentication needed

## 🛠️ Development

### Server Files
- `server.py` - Entry point
- `api/app.py` - FastAPI application
- `api/models.py` - Request/response models  
- `api/routes.py` - All 13 endpoint definitions

### Testing
- `test_server.py` - Basic server functionality test
- Real API integration (no mocks)
- Live database connections

## 📊 Performance

- **Async-first**: All endpoints use async/await
- **Fast startup**: ~2-3 seconds
- **Response times**: 
  - Health check: ~5ms
  - Inventory queries: ~500-1000ms
  - Calendar operations: ~200-800ms

## 🎯 Voice Agent Integration

Perfect for voice agent frameworks:
- **Consistent POST endpoints**: Uniform interface
- **Structured responses**: Predictable JSON format
- **Parameter validation**: Clear error messages
- **Comprehensive docs**: Auto-generated OpenAPI spec
- **CORS enabled**: Cross-origin requests supported

## 📈 Production Readiness

This MVP server provides:
- ✅ All 13 tools exposed via HTTP
- ✅ Real database/API integration
- ✅ Proper error handling
- ✅ Request validation
- ✅ Auto-generated documentation
- ✅ CORS support
- ✅ Async architecture

Ready for voice agent integration and end-to-end testing!

