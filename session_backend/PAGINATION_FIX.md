# Pagination Fix Documentation

## Issue
The session backend API uses `page` and `page_size` parameters for pagination, while the Strands `SessionRepository` interface expects `limit` and `offset` parameters.

## Solution
The `SyncPostgreSQLSessionRepository.list_messages()` method now translates between these two pagination schemes:

### Translation Logic

#### Case 1: Both limit and offset provided
```python
limit=2, offset=4
→ page_size=2, page=3  # (4 // 2) + 1
```

#### Case 2: Only limit provided
```python
limit=5, offset=None
→ page_size=5, page=1
```

#### Case 3: Only offset provided
```python
limit=None, offset=3
→ page_size=1000, page=1  # Fetch all, then slice
→ messages[3:]  # Skip first 3 messages
```

#### Case 4: Neither provided
```python
limit=None, offset=None
→ No params sent (API returns default page)
```

## Implementation

```python
def list_messages(self, session_id: str, agent_id: str, 
                 limit: Optional[int] = None, 
                 offset: Optional[int] = None, 
                 **kwargs: Any) -> List[SessionMessage]:
    """List messages in chronological order with pagination via API call."""
    params = {}
    
    if limit is not None or offset is not None:
        page_size = limit if limit is not None else 10
        offset_val = offset if offset is not None else 0
        
        if offset is not None and limit is None:
            # Special case: fetch all and slice
            page = 1
            page_size = 1000  # Max allowed by API
            params["page"] = page
            params["page_size"] = page_size
        else:
            # Normal case: calculate page number
            page = (offset_val // page_size) + 1
            params["page"] = page
            params["page_size"] = page_size
    
    response = self.session.get(
        f"{self.base_url}/api/v1/sessions/{session_id}/agents/{agent_id}/messages",
        params=params,
        timeout=self.timeout
    )
    
    if response.status_code == 200:
        response_data = response.json()
        messages_data = response_data.get("messages", response_data)
        messages = [SessionMessage.from_dict(m) for m in messages_data]
        
        # Post-process for offset-only case
        if offset is not None and limit is None:
            messages = messages[offset:]
        
        return messages
```

## Testing
All pagination scenarios are tested in `test-session-agent/test_api_comprehensive.py`:

- ✅ List all messages (no params)
- ✅ List with limit only (`limit=2`)
- ✅ List with offset only (`offset=1`)
- ✅ List with both (`limit=1, offset=1`)

## Files Updated
- `session_backend/postgresql_session_repository.py`
- `test-session-agent/agent/postgresql_session_repository.py`

Both files contain identical implementations of the pagination fix.
