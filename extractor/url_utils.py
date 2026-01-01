"""
URL utility functions for cleaning and processing URLs
"""

from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


def remove_utm_parameters(url):
    """
    Remove all UTM parameters from a URL (both query string and fragment).
    
    Args:
        url: The URL string to clean
        
    Returns:
        The URL with all utm_* parameters removed
        
    Example:
        >>> remove_utm_parameters('https://example.com/page?utm_source=google&utm_medium=cpc&id=123')
        'https://example.com/page?id=123'
        >>> remove_utm_parameters('https://example.com/page#utm_source=newsletter&utm_medium=email')
        'https://example.com/page'
    """
    if not url:
        return url
    
    try:
        parsed = urlparse(url)
        
        # Clean query parameters
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        cleaned_params = {
            k: v for k, v in query_params.items() 
            if not k.lower().startswith('utm_')
        }
        cleaned_query = urlencode(cleaned_params, doseq=True)
        
        # Clean fragment if it contains UTM parameters
        cleaned_fragment = parsed.fragment
        if cleaned_fragment and 'utm_' in cleaned_fragment.lower():
            # Parse fragment as if it were a query string
            fragment_params = parse_qs(cleaned_fragment, keep_blank_values=True)
            cleaned_fragment_params = {
                k: v for k, v in fragment_params.items()
                if not k.lower().startswith('utm_')
            }
            if cleaned_fragment_params:
                cleaned_fragment = urlencode(cleaned_fragment_params, doseq=True)
            else:
                # If all fragment params were UTM, remove fragment entirely
                cleaned_fragment = ''
        
        # Reconstruct the URL
        cleaned_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            cleaned_query,
            cleaned_fragment
        ))
        
        return cleaned_url
    except Exception:
        # If parsing fails, return original URL
        return url
