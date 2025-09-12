# Logging Implementation Guide

This document describes the comprehensive logging system implemented across the FastAPI job portal application.

## Overview

The logging system provides:
- **Structured logging** with JSON format for production
- **Colored console output** for development
- **Request/response tracking** with unique request IDs
- **Performance monitoring** with execution time tracking
- **Security event logging** for authentication and authorization
- **Database operation logging** for audit trails
- **Error tracking** with full stack traces

## Log Files

The system creates the following log files in the `logs/` directory:

- `app.log` - General application logs (INFO level and above)
- `error.log` - Error logs only (ERROR level and above)
- `app.json` - Structured JSON logs for log aggregation systems

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=detailed               # detailed, simple, json
LOG_TO_FILE=true                  # Enable/disable file logging
LOG_FILE_MAX_SIZE_MB=10           # Maximum log file size before rotation
LOG_FILE_BACKUP_COUNT=5           # Number of backup files to keep
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General application flow information
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error conditions that don't stop the application
- **CRITICAL**: Serious errors that might stop the application

## Logging Components

### 1. Request Logging Middleware

Automatically logs all HTTP requests and responses:

```python
# Example log entry
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.middleware",
  "message": "Request completed",
  "method": "POST",
  "path": "/business/",
  "status_code": 201,
  "duration_ms": 245.67,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123"
}
```

### 2. Business Logic Logging

Service methods log their operations:

```python
# Example from JobService.create_job()
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.business_service",
  "message": "Job created successfully: 456",
  "operation": "create_job",
  "user_id": "123",
  "job_id": "456",
  "title": "Software Engineer"
}
```

### 3. Security Event Logging

Authentication and authorization events:

```python
# Example security log
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "WARNING",
  "logger": "app.security",
  "message": "Security event: login_failed",
  "event": "login_failed",
  "email": "user@example.com",
  "reason": "invalid_credentials",
  "ip_address": "192.168.1.100"
}
```

### 4. Performance Logging

Track execution times for operations:

```python
# Example performance log
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.performance",
  "message": "Performance: get_all_jobs",
  "operation": "get_all_jobs",
  "duration_ms": 156.78,
  "count": 25
}
```

### 5. Database Operation Logging

Track database interactions:

```python
# Example database log
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.database",
  "message": "Database operation: INSERT",
  "operation": "INSERT",
  "table": "business",
  "record_id": "456"
}
```

## Using the Logger in Your Code

### Basic Usage

```python
from app.utils.logger import get_logger

logger = get_logger("your_module_name")

# Basic logging
logger.info("Operation completed successfully")
logger.warning("Potential issue detected")
logger.error("Operation failed", exc_info=True)
```

### Structured Logging

```python
from app.utils.logger import log_business_operation, log_performance

# Business operation logging
log_business_operation("create_user", user_id="123", email="user@example.com")

# Performance logging
start_time = time.time()
# ... your operation ...
duration_ms = (time.time() - start_time) * 1000
log_performance("complex_operation", duration_ms, records_processed=100)
```

### Request Context Logging

```python
from app.utils.logger import RequestContext

# In your route handler
with RequestContext(request_id="abc123", user_id="456", endpoint="POST /jobs") as ctx:
    ctx.log_request("POST", "/jobs", user_id="456")
    
    # Your business logic here
    
    ctx.log_response(201, 245.67)
```

## Log Analysis

### Development

For development, logs are displayed in the console with colors:
- 🔵 DEBUG: Cyan
- 🟢 INFO: Green
- 🟡 WARNING: Yellow
- 🔴 ERROR: Red
- 🟣 CRITICAL: Magenta

### Production

In production, use the JSON logs for analysis:

```bash
# View recent errors
tail -f logs/error.log

# Parse JSON logs with jq
cat logs/app.json | jq '.level == "ERROR"'

# Monitor performance
cat logs/app.json | jq 'select(.logger == "app.performance") | .duration_ms'
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Error Rate**: Count of ERROR level logs per time period
2. **Response Time**: Average duration_ms from request logs
3. **Failed Logins**: Security events with event_type="login_failed"
4. **Database Performance**: Duration of database operations

### Example Monitoring Queries

```bash
# Count errors in the last hour
grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" logs/error.log | wc -l

# Average response time
cat logs/app.json | jq 'select(.logger == "app.middleware" and .duration_ms != null) | .duration_ms' | awk '{sum+=$1; count++} END {print sum/count}'

# Failed login attempts
grep "login_failed" logs/app.json | jq '.email' | sort | uniq -c
```

## Best Practices

### 1. Log Levels

- Use **DEBUG** for detailed diagnostic information
- Use **INFO** for general application flow
- Use **WARNING** for potentially harmful situations
- Use **ERROR** for error events that don't stop the application
- Use **CRITICAL** for serious errors

### 2. Sensitive Information

Never log:
- Passwords or password hashes
- Credit card numbers
- Social security numbers
- API keys or secrets

### 3. Performance

- Use structured logging for better performance
- Avoid string formatting in log messages when possible
- Use appropriate log levels to reduce noise

### 4. Context

Always include relevant context:
- User ID for user-related operations
- Request ID for request tracking
- Operation type for business logic
- Duration for performance monitoring

## Troubleshooting

### Common Issues

1. **Log files not created**: Check directory permissions for `logs/` folder
2. **No console output**: Verify `LOG_LEVEL` is set appropriately
3. **Large log files**: Adjust `LOG_FILE_MAX_SIZE_MB` and `LOG_FILE_BACKUP_COUNT`

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

This will show detailed logs including SQL queries and internal operations.

## Integration with External Systems

### Log Aggregation

The JSON log format is compatible with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Fluentd**
- **Splunk**
- **Datadog**
- **New Relic**

### Example Logstash Configuration

```ruby
input {
  file {
    path => "/path/to/logs/app.json"
    codec => "json"
  }
}

filter {
  if [logger] == "app.middleware" {
    mutate {
      add_tag => ["http_request"]
    }
  }
  
  if [logger] == "app.security" {
    mutate {
      add_tag => ["security_event"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "job-portal-logs-%{+YYYY.MM.dd}"
  }
}
```

This comprehensive logging system provides full visibility into your application's behavior, performance, and security events, making it easier to monitor, debug, and maintain your FastAPI job portal application.
