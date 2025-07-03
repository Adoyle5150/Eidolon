# Azure Bing API Setup for Web Searcher

This document explains how to set up the Azure Bing API for the enhanced web searcher.

## Prerequisites

1. Azure subscription
2. Bing Search API resource created in Azure

## Setup Steps

### 1. Create Bing Search API Resource

1. Go to the Azure Portal (https://portal.azure.com)
2. Create a new resource
3. Search for "Bing Search v7"
4. Create the resource with your preferred settings

### 2. Get API Key and Endpoint

1. Go to your Bing Search API resource in Azure Portal
2. Navigate to "Keys and Endpoint" section
3. Copy the API Key (Key 1 or Key 2)
4. Copy the Endpoint URL

### 3. Set Environment Variables

Set the following environment variables:

**Windows (PowerShell):**
```powershell
$env:BING_API_KEY="your_api_key_here"
$env:BING_ENDPOINT="https://your-resource-name.cognitiveservices.azure.com"
```

**Windows (Command Prompt):**
```cmd
set BING_API_KEY=your_api_key_here
set BING_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com
```

**Linux/Mac:**
```bash
export BING_API_KEY="your_api_key_here"
export BING_ENDPOINT="https://your-resource-name.cognitiveservices.azure.com"
```

### 4. Test the Setup

Run the following command to test if the API is working:

```python
from web.searcher import web_search_simple
result = web_search_simple("test query")
print(result)
```

## Configuration

The searcher will automatically use the Azure Bing API when the environment variables are set. If they are not set, you'll see a warning message and the search will fail.

## API Limits

- Azure Bing Search API has usage limits based on your subscription tier
- Monitor your usage in the Azure Portal
- Consider implementing rate limiting for production use

## Troubleshooting

1. **"Bing API key or endpoint is not set"**: Make sure environment variables are set correctly
2. **API errors**: Check your Azure subscription and API key validity
3. **Rate limiting**: Implement delays between requests if needed

## Migration from DuckDuckGo

This implementation replaces the previous DuckDuckGo and Bing scraping functionality with the official Azure Bing API, providing:

- More reliable search results
- Better rate limits
- Official API support
- Improved content quality 