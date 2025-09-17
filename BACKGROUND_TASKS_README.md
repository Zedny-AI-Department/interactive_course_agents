# Background Task Processing Implementation

This implementation adds background task processing to handle long-running video processing operations without blocking the API responses.

## New Features

- **Background Processing**: Video processing runs in background tasks
- **Task Status Tracking**: Monitor task progress and status
- **User Isolation**: Each user can have up to 5 concurrent tasks
- **Resource Management**: Global server task limits prevent overload
- **Persistence**: Tasks survive server restarts (stored in Redis)

## API Changes

### 1. Main Endpoint (Now Async)

**POST** `/process/srt_media/`

**Headers Required:**
```
X-User-ID: your_user_id
```

**Response:**
```json
{
  "task_id": "user123:abc-def-123", 
  "status": "pending",
  "message": "Task created successfully. Use the task_id to track progress."
}
```

### 2. Track Task Status

**GET** `/tasks/{task_id}/status`

**Headers Required:**
```
X-User-ID: your_user_id
```

**Response:**
```json
{
  "task_id": "user123:abc-def-123",
  "status": "processing",
  "stage": "aligning", 
  "progress": 75,
  "created_at": "2025-01-17T10:00:00Z",
  "updated_at": "2025-01-17T10:05:00Z"
}
```

**Task Status Values:**
- `pending`: Task queued but not started
- `processing`: Task is being processed
- `completed`: Task finished successfully
- `failed`: Task failed with error
- `cancelled`: Task was cancelled

**Task Stages:**
- `queued`: Waiting to start
- `transcribing`: Extracting transcription
- `processing_llm`: LLM processing stage
- `aligning`: Aligning with video
- `completed`: All stages finished

### 3. Get Task Result

**GET** `/tasks/{task_id}/result`

**Headers Required:**
```
X-User-ID: your_user_id
```

**Response** (when completed):
```json
{
  "task_id": "user123:abc-def-123",
  "status": "completed", 
  "result": {
    "paragraphs": [...] // Your processed data
  }
}
```

### 4. Get All User Tasks

**GET** `/users/me/tasks?include_completed=true`

**Headers Required:**
```
X-User-ID: your_user_id
```

**Response:**
```json
{
  "user_id": "user123",
  "active_tasks": [...],
  "completed_tasks": [...],
  "total_active": 2,
  "total_completed": 5
}
```

### 5. Cancel Task

**DELETE** `/tasks/{task_id}`

**Headers Required:**
```
X-User-ID: your_user_id
```

### 6. Legacy Sync Endpoint

**POST** `/process/srt_media/sync`

The original synchronous endpoint is still available for backward compatibility.

## Frontend Integration

### Example JavaScript Implementation

```javascript
class VideoProcessingClient {
  constructor(apiBase, userId) {
    this.apiBase = apiBase;
    this.userId = userId;
  }

  async createTask(srtFile, mediaFile) {
    const formData = new FormData();
    formData.append('srt_file', srtFile);
    formData.append('media_file', mediaFile);

    const response = await fetch(`${this.apiBase}/process/srt_media/`, {
      method: 'POST',
      headers: { 'X-User-ID': this.userId },
      body: formData
    });

    return response.json();
  }

  async pollTaskStatus(taskId, onProgress) {
    const poll = async () => {
      const response = await fetch(`${this.apiBase}/tasks/${taskId}/status`, {
        headers: { 'X-User-ID': this.userId }
      });
      
      const data = await response.json();
      onProgress(data);

      if (data.status === 'completed') {
        return await this.getTaskResult(taskId);
      } else if (data.status === 'failed') {
        throw new Error(data.error_message || 'Task failed');
      } else if (data.status !== 'cancelled') {
        // Continue polling
        setTimeout(poll, 3000); // Poll every 3 seconds
      }
    };

    return poll();
  }

  async getTaskResult(taskId) {
    const response = await fetch(`${this.apiBase}/tasks/${taskId}/result`, {
      headers: { 'X-User-ID': this.userId }
    });
    return response.json();
  }

  async getUserTasks() {
    const response = await fetch(`${this.apiBase}/users/me/tasks`, {
      headers: { 'X-User-ID': this.userId }
    });
    return response.json();
  }
}

// Usage example
const client = new VideoProcessingClient('http://localhost:8000', 'user123');

async function processVideo(srtFile, mediaFile) {
  try {
    // Create task
    const task = await client.createTask(srtFile, mediaFile);
    console.log('Task created:', task.task_id);

    // Poll for completion
    const result = await client.pollTaskStatus(task.task_id, (status) => {
      console.log(`Progress: ${status.progress}% - ${status.stage}`);
    });

    console.log('Processing completed:', result);
    return result;
  } catch (error) {
    console.error('Processing failed:', error);
  }
}
```

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379

# Task Limits
MAX_CONCURRENT_TASKS_PER_USER=5
MAX_GLOBAL_CONCURRENT_TASKS=20
```

### Redis Setup

Make sure Redis is running:

```bash
# Install Redis (Ubuntu/Debian)
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:latest
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Error Handling

### Common Error Responses

**429 Too Many Requests** - User has reached 5 concurrent task limit:
```json
{
  "detail": "Maximum 5 concurrent tasks per user exceeded"
}
```

**503 Service Unavailable** - Server is at capacity:
```json
{
  "detail": "Server is busy, please try again later"
}
```

**401 Unauthorized** - Missing user identification:
```json
{
  "detail": "Missing X-User-ID header. Please provide user identification."
}
```

**404 Not Found** - Task doesn't exist:
```json
{
  "detail": "Task not found"
}
```

**403 Forbidden** - Task belongs to different user:
```json
{
  "detail": "Access denied"
}
```

## Monitoring

### Task Metrics

You can monitor task metrics by checking Redis:

```bash
# Active tasks count
redis-cli GET global:active_tasks_count

# User's active tasks
redis-cli SMEMBERS user:user123:active_tasks

# Task data
redis-cli HGET task:user123:abc-123 data
```

## Production Considerations

1. **Authentication**: Replace the simple `X-User-ID` header with proper JWT authentication
2. **Rate Limiting**: Add additional rate limiting per user/IP
3. **Monitoring**: Add proper logging and metrics collection
4. **Cleanup**: Implement periodic cleanup of old completed tasks
5. **Security**: Validate file types and sizes before processing
6. **Scaling**: Consider adding multiple worker processes or servers

## Migration from Sync to Async

If you have existing frontend code using the sync endpoint:

1. **Immediate**: Use `/process/srt_media/sync` (no changes needed)
2. **Gradual**: Update frontend to use new async endpoints
3. **Future**: Remove sync endpoint once migration is complete