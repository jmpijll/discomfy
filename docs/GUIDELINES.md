# Discord ComfyUI Bot - Development Guidelines

## Core Principles

### 1. Modular Architecture
- **bot.py**: Contains ONLY Discord-related logic (commands, interactions, UI)
- **image_gen.py**: Handles all image generation logic and ComfyUI API calls
- **video_gen.py**: Handles all video generation logic and ComfyUI API calls
- **workflows/**: Contains JSON workflow files (ComfyUI API exports)
- **config.py**: Centralized configuration management
- No cross-contamination between modules

### 2. Configuration Management
- All configurable values must be in config files, never hardcoded
- Discord bot token, ComfyUI URL, and API keys in environment variables
- User-adjustable parameters must be mapped to workflow JSON fields
- Configuration validation on startup
- Support for multiple workflow configurations

### 3. Error Handling & Reliability
- Comprehensive try-catch blocks for all external API calls
- Graceful degradation when ComfyUI is unavailable
- User-friendly error messages (no technical stack traces to users)
- Logging all errors for debugging
- Bot must never crash from user input

### 4. File Management
- All outputs saved to `outputs/` folder
- Maintain only last 50 files (automatic cleanup)
- Unique filenames to prevent conflicts
- Proper file type validation
- Handle Discord file size limits (8MB default, 25MB Nitro)

### 5. User Experience
- Slash commands for primary interactions
- Interactive buttons for post-generation actions
- Progress indicators for long operations
- Clear parameter descriptions and validation
- Helpful error messages with suggestions

### 6. Performance & Scalability
- Asynchronous operations for all I/O
- Queue system for handling multiple requests
- Rate limiting to prevent abuse
- Memory-efficient image/video processing
- Proper resource cleanup

### 7. Code Quality
- Type hints for all functions
- Docstrings for all classes and functions
- Consistent naming conventions (snake_case)
- Maximum function length: 50 lines
- Single responsibility principle
- No global variables (except configuration)

### 8. Testing & Validation
- Each phase must be fully testable
- Validate all user inputs
- Test with various workflow JSON files
- Verify Discord integration at each step
- Test error scenarios

### 9. Security
- Validate all user inputs
- Sanitize file names and paths
- Rate limiting per user
- No execution of user-provided code
- Secure handling of API keys

### 10. Documentation
- Inline comments for complex logic
- README with complete setup instructions
- API documentation for all functions
- Troubleshooting guide
- Example usage for all features

### 11. Git Version Control (MANDATORY)
- Project MUST be versioned in Git from the start
- Commit after every completed step/feature
- Push commits after each step (local repository for now)
- Meaningful commit messages following format: "feat: description" or "fix: description"
- No commits with incomplete or broken functionality
- Tag major milestones and phase completions
- Maintain clean commit history

## Specific Implementation Rules

### Progress Tracking Implementation (MANDATORY)
**Real-time progress tracking using ComfyUI WebSocket API with HTTP polling fallback**

#### WebSocket Integration Requirements:
- **Client ID Handling**: Must retrieve `client_id` from ComfyUI status message before queuing prompts
- **Proper Connection**: Connect to WebSocket first, get client_id, then submit prompt with that client_id
- **Message Types**: Handle `progress`, `executing`, `executed`, `execution_success`, and `status` message types
- **Step-Based Progress**: Calculate percentage based on sampling steps only, not node execution
- **Fallback Support**: Use HTTP polling if WebSocket connection fails or hangs

#### Implementation Pattern:
```python
# 1. Connect to WebSocket and get client_id
async with websockets.connect(ws_url) as websocket:
    status_message = await websocket.recv()
    client_id = json.loads(status_message)['client_id']

# 2. Submit prompt with client_id
response = await session.post(f"{base_url}/prompt", json={
    "client_id": client_id,
    "prompt": workflow
})

# 3. Track progress via WebSocket messages
while True:
    message = await websocket.recv()
    data = json.loads(message)
    
    if data['type'] == 'progress':
        # Update step progress (e.g., 152/161)
        current_step = data['data']['value']
        total_steps = data['data']['max']
        
    elif data['type'] == 'executing':
        # Track node execution
        node_id = data['data']['node']
        
    elif data['type'] == 'execution_success':
        # Generation completed
        break
```

#### Progress Calculation Rules:
- **Before First Sampling Step**: Show "Loading..." or "Preparing..." (0% progress)
- **During Sampling**: Calculate percentage as `(current_step / total_steps) * 100`
- **Multiple Sampling Nodes**: For video generation, handle multiple KSampler nodes with different step counts
- **Final Processing**: Show 95-100% for post-sampling nodes (VAE decode, save, etc.)

#### Error Handling Requirements:
- **WebSocket Timeout**: 5-second timeout for client_id retrieval, 10-second for messages
- **Connection Failure**: Graceful fallback to HTTP polling every 1 second
- **Message Loss**: HTTP polling should continue if WebSocket stops sending messages
- **Rate Limiting**: Ensure 1-second intervals don't overwhelm Discord API

#### Progress Display Format:
```
🎨 Generating Image
📊 67.3% ████████████░░░░░░░░
🔄 Sampling (152/161)
⏱️ Elapsed: 1m 23s | ETA: 32s
🎯 Node: KSampler
```

#### Video Generation Specifics:
- **Extended Timeout**: 10 minutes for video workflows vs 2 minutes for images
- **Multiple Sampling Phases**: Handle different step counts for different video generation stages
- **Progress Aggregation**: Combine multiple sampling nodes into single progress percentage

### Discord Integration
- Use discord.py library with slash commands
- Implement proper permission checks
- Handle Discord rate limits gracefully
- Use embeds for rich responses
- Implement button interactions for actions

### ComfyUI Integration
- Use requests library for API calls
- Implement proper timeout handling
- Parse workflow JSON dynamically
- Map user parameters to workflow nodes
- Handle ComfyUI queue system

### Workflow Management
- JSON files must be valid ComfyUI API exports
- Support dynamic parameter replacement
- Validate workflow compatibility
- Allow multiple workflow selection
- Implement workflow versioning

### Image Processing
- Use PIL for image manipulation
- Create collages for multiple images
- Implement proper image compression
- Handle various image formats
- Maintain aspect ratios

### Video Processing
- Support common video formats (MP4, WebM)
- Implement video compression for Discord limits
- Handle video thumbnails
- Support image-to-video conversion
- Proper video metadata handling

## Prohibited Practices
- No hardcoded values (except constants)
- No blocking operations in main thread
- No direct file system access without validation
- No user input execution
- No global state modification
- No breaking changes without version updates
- No deviation from modular architecture
- No skipping error handling
- No incomplete features in releases

## Code Review Checklist
- [ ] Follows modular architecture
- [ ] Proper error handling implemented
- [ ] Type hints and docstrings present
- [ ] No hardcoded values
- [ ] Async/await used correctly
- [ ] User input validated
- [ ] Memory leaks prevented
- [ ] Discord limits respected
- [ ] Configuration properly used
- [ ] Tests can be written and passed

## Version Control
- Meaningful commit messages using conventional format
- Feature branches for new functionality
- No direct commits to main branch
- Tag releases with version numbers
- Maintain changelog
- **MANDATORY**: Commit and push after every completed step
- **MANDATORY**: All code must be in Git before proceeding to next step

These guidelines are mandatory and must not be deviated from without explicit permission. 