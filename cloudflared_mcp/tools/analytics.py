from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import READ_ONLY


@mcp.tool(annotations=READ_ONLY)
async def get_traffic_analytics(
    zone_id: str,
    since: str = "-1440",
    until: str = "0",
) -> dict:
    """Get traffic analytics overview for a zone — requests, bandwidth, threats, and pageviews.

    since/until: ISO 8601 datetime (e.g. "2024-01-01T00:00:00Z") or a negative integer
    representing minutes from now (e.g. "-1440" = last 24 h, "-10080" = last 7 days).
    Default: last 24 hours.
    """
    client = get_client()
    return await client.request(
        "GET",
        f"/zones/{zone_id}/analytics/dashboard",
        params={"since": since, "until": until},
    )


@mcp.tool(annotations=READ_ONLY)
async def get_http_requests(
    zone_id: str,
    since: str = "-1440",
    until: str = "0",
) -> dict:
    """Get HTTP request counts for a zone — total, cached, and uncached — broken down by
    content type, country, HTTP status code, and SSL usage.

    since/until: ISO 8601 datetime or negative-integer minutes (e.g. "-1440" = last 24 h).
    """
    client = get_client()
    data = await client.request(
        "GET",
        f"/zones/{zone_id}/analytics/dashboard",
        params={"since": since, "until": until},
    )
    result = data.get("result", {})
    return {
        "success": data.get("success"),
        "result": {
            "totals": result.get("totals", {}).get("requests", {}),
            "timeseries": [
                {"timestamp": ts.get("until"), "requests": ts.get("requests", {})}
                for ts in result.get("timeseries", [])
            ],
        },
    }


@mcp.tool(annotations=READ_ONLY)
async def get_bandwidth_usage(
    zone_id: str,
    since: str = "-1440",
    until: str = "0",
) -> dict:
    """Get bandwidth usage for a zone — total, cached, and uncached bytes — broken down by
    content type, country, and SSL usage.

    since/until: ISO 8601 datetime or negative-integer minutes (e.g. "-1440" = last 24 h).
    """
    client = get_client()
    data = await client.request(
        "GET",
        f"/zones/{zone_id}/analytics/dashboard",
        params={"since": since, "until": until},
    )
    result = data.get("result", {})
    return {
        "success": data.get("success"),
        "result": {
            "totals": result.get("totals", {}).get("bandwidth", {}),
            "timeseries": [
                {"timestamp": ts.get("until"), "bandwidth": ts.get("bandwidth", {})}
                for ts in result.get("timeseries", [])
            ],
        },
    }


@mcp.tool(annotations=READ_ONLY)
async def get_cache_analytics(
    zone_id: str,
    since: str = "-1440",
    until: str = "0",
) -> dict:
    """Get cache performance analytics for a zone — cached vs. uncached requests and bytes,
    including computed cache-hit ratios.

    since/until: ISO 8601 datetime or negative-integer minutes (e.g. "-1440" = last 24 h).
    """
    client = get_client()
    data = await client.request(
        "GET",
        f"/zones/{zone_id}/analytics/dashboard",
        params={"since": since, "until": until},
    )
    result = data.get("result", {})
    totals = result.get("totals", {})
    req = totals.get("requests", {})
    bw = totals.get("bandwidth", {})
    all_req = req.get("all", 0)
    all_bw = bw.get("all", 0)
    return {
        "success": data.get("success"),
        "result": {
            "totals": {
                "requests": {
                    "all": all_req,
                    "cached": req.get("cached", 0),
                    "uncached": req.get("uncached", 0),
                    "cache_hit_ratio": round(req.get("cached", 0) / all_req, 4) if all_req else 0,
                },
                "bandwidth": {
                    "all": all_bw,
                    "cached": bw.get("cached", 0),
                    "uncached": bw.get("uncached", 0),
                    "cache_hit_ratio": round(bw.get("cached", 0) / all_bw, 4) if all_bw else 0,
                },
            },
            "timeseries": [
                {
                    "timestamp": ts.get("until"),
                    "requests_cached": ts.get("requests", {}).get("cached", 0),
                    "requests_uncached": ts.get("requests", {}).get("uncached", 0),
                    "bandwidth_cached": ts.get("bandwidth", {}).get("cached", 0),
                    "bandwidth_uncached": ts.get("bandwidth", {}).get("uncached", 0),
                }
                for ts in result.get("timeseries", [])
            ],
        },
    }


@mcp.tool(annotations=READ_ONLY)
async def get_top_countries(
    zone_id: str,
    since: str = "-1440",
    until: str = "0",
) -> dict:
    """Get traffic analytics broken down by country and Cloudflare data center (colocation),
    including requests, bandwidth, and threats per location.

    since/until: ISO 8601 datetime or negative-integer minutes (e.g. "-1440" = last 24 h).
    """
    client = get_client()
    return await client.request(
        "GET",
        f"/zones/{zone_id}/analytics/colos",
        params={"since": since, "until": until},
    )


@mcp.tool(annotations=READ_ONLY)
async def get_top_paths(
    zone_id: str,
    since: str,
    until: str,
    limit: int = 10,
) -> dict:
    """Get the most-requested URL paths for a zone via the Cloudflare GraphQL Analytics API.

    since/until: ISO 8601 datetime strings (e.g. "2024-01-01T00:00:00Z"). Required.
    limit: Number of top paths to return (max 100, default 10).
    """
    client = get_client()
    query = """
    query TopPaths($zoneTag: string, $since: Time, $until: Time, $limit: Int) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          httpRequestsAdaptiveGroups(
            limit: $limit
            filter: {datetime_geq: $since, datetime_leq: $until}
            orderBy: [count_DESC]
          ) {
            count
            dimensions {
              clientRequestPath
            }
          }
        }
      }
    }
    """
    return await client.graphql(
        query,
        {"zoneTag": zone_id, "since": since, "until": until, "limit": limit},
    )


@mcp.tool(annotations=READ_ONLY)
async def get_security_analytics(
    zone_id: str,
    since: str = "-1440",
    until: str = "0",
) -> dict:
    """Get security and threat analytics for a zone — total threats, threat types,
    and threat breakdown by country.

    since/until: ISO 8601 datetime or negative-integer minutes (e.g. "-1440" = last 24 h).
    """
    client = get_client()
    data = await client.request(
        "GET",
        f"/zones/{zone_id}/analytics/dashboard",
        params={"since": since, "until": until},
    )
    result = data.get("result", {})
    return {
        "success": data.get("success"),
        "result": {
            "totals": result.get("totals", {}).get("threats", {}),
            "timeseries": [
                {"timestamp": ts.get("until"), "threats": ts.get("threats", {})}
                for ts in result.get("timeseries", [])
            ],
        },
    }


@mcp.tool(annotations=READ_ONLY)
async def get_bot_analytics(
    zone_id: str,
    since: str,
    until: str,
    limit: int = 10,
) -> dict:
    """Get bot traffic analytics via the Cloudflare GraphQL Analytics API.
    Returns bot management decision breakdown and top hosts targeted by bots.

    since/until: ISO 8601 datetime strings (e.g. "2024-01-01T00:00:00Z"). Required.
    limit: Number of groups to return (default 10).
    Requires Bot Management or equivalent subscription.
    """
    client = get_client()
    query = """
    query BotAnalytics($zoneTag: string, $since: Time, $until: Time, $limit: Int) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          httpRequestsAdaptiveGroups(
            limit: $limit
            filter: {datetime_geq: $since, datetime_leq: $until}
            orderBy: [count_DESC]
          ) {
            count
            dimensions {
              botManagementDecision
              clientRequestHTTPHost
            }
          }
        }
      }
    }
    """
    return await client.graphql(
        query,
        {"zoneTag": zone_id, "since": since, "until": until, "limit": limit},
    )


@mcp.tool(annotations=READ_ONLY)
async def get_origin_performance(
    zone_id: str,
    since: str = "-1440",
    until: str = "0",
) -> dict:
    """Get origin server performance analytics — how much traffic bypasses the cache and
    reaches your origin, vs. traffic served directly from Cloudflare's edge.

    since/until: ISO 8601 datetime or negative-integer minutes (e.g. "-1440" = last 24 h).
    """
    client = get_client()
    data = await client.request(
        "GET",
        f"/zones/{zone_id}/analytics/dashboard",
        params={"since": since, "until": until},
    )
    result = data.get("result", {})
    totals = result.get("totals", {})
    req = totals.get("requests", {})
    bw = totals.get("bandwidth", {})
    return {
        "success": data.get("success"),
        "result": {
            "totals": {
                "requests_to_origin": req.get("uncached", 0),
                "requests_from_cache": req.get("cached", 0),
                "bandwidth_to_origin": bw.get("uncached", 0),
                "bandwidth_from_cache": bw.get("cached", 0),
            },
            "timeseries": [
                {
                    "timestamp": ts.get("until"),
                    "requests_to_origin": ts.get("requests", {}).get("uncached", 0),
                    "bandwidth_to_origin": ts.get("bandwidth", {}).get("uncached", 0),
                }
                for ts in result.get("timeseries", [])
            ],
        },
    }


@mcp.tool(annotations=READ_ONLY)
async def get_analytics_by_date(
    zone_id: str,
    since: str = "-10080",
    until: str = "0",
) -> dict:
    """Get time-series analytics for a zone — requests, bandwidth, threats, and pageviews
    broken down by time interval over the requested period.

    since/until: ISO 8601 datetime or negative-integer minutes
    (e.g. "-10080" = last 7 days, "-1440" = last 24 h). Default: last 7 days.
    """
    client = get_client()
    data = await client.request(
        "GET",
        f"/zones/{zone_id}/analytics/dashboard",
        params={"since": since, "until": until},
    )
    result = data.get("result", {})
    return {
        "success": data.get("success"),
        "result": {
            "period": {
                "since": result.get("totals", {}).get("since"),
                "until": result.get("totals", {}).get("until"),
            },
            "timeseries": result.get("timeseries", []),
        },
    }
