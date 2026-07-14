from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY


@mcp.tool(annotations=READ_ONLY)
async def get_ssl_verification(zone_id: str) -> dict:
    """Get SSL/TLS certificate verification status/details for a zone."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}/ssl/verification")


@mcp.tool(annotations=READ_ONLY)
async def list_custom_certificates(
    zone_id: str,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    """List custom (uploaded) SSL certificates for a zone.

    per_page: items per page (Cloudflare maximum for this endpoint is 50). page: 1-based.
    Check result_info.total_count for the true total and result_info.total_pages
    to detect whether more pages exist.
    """
    client = get_client()
    return await client.request(
        "GET",
        f"/zones/{zone_id}/custom_certificates",
        params={"page": page, "per_page": per_page},
    )


@mcp.tool(annotations=CREATE)
async def upload_custom_certificate(
    zone_id: str, certificate: str, private_key: str, bundle_method: str = "ubiquitous"
) -> dict:
    """Upload a custom SSL certificate + private key for a zone."""
    client = get_client()
    body = {
        "certificate": certificate,
        "private_key": private_key,
        "bundle_method": bundle_method,
    }
    return await client.request("POST", f"/zones/{zone_id}/custom_certificates", json_body=body)


@mcp.tool(annotations=DELETE)
async def delete_custom_certificate(zone_id: str, certificate_id: str) -> dict:
    """Delete a custom SSL certificate from a zone."""
    client = get_client()
    return await client.request(
        "DELETE", f"/zones/{zone_id}/custom_certificates/{certificate_id}"
    )


@mcp.tool(annotations=CREATE)
async def create_origin_ca_certificate(
    hostnames: list[str], csr: str, request_type: str = "origin-rsa", requested_validity: int = 5475
) -> dict:
    """Create an Origin CA certificate for securing traffic between Cloudflare and your origin server."""
    client = get_client()
    body = {
        "hostnames": hostnames,
        "csr": csr,
        "request_type": request_type,
        "requested_validity": requested_validity,
    }
    return await client.request("POST", "/certificates", json_body=body)


@mcp.tool(annotations=READ_ONLY)
async def list_origin_ca_certificates(
    zone_id: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> dict:
    """List Origin CA certificates, optionally filtered by zone.

    per_page: items per page. page: 1-based.
    When page=1 (default), ALL pages are fetched automatically so result[].length always
    equals result_info.total_count. Pass page>1 to fetch a specific page only.
    result_info.total_count reflects only the zone_id-filtered subset when zone_id is supplied.
    """
    client = get_client()
    params: dict = {"page": page, "per_page": per_page}
    if zone_id:
        params["zone_id"] = zone_id
    if page != 1:
        return await client.request("GET", "/certificates", params=params)
    return await client.request_all_pages("GET", "/certificates", params=params)
