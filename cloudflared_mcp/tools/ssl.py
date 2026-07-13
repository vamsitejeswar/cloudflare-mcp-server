from cloudflared_mcp.app import mcp
from cloudflared_mcp.client import get_client
from cloudflared_mcp.annotations import CREATE, DELETE, READ_ONLY


@mcp.tool(annotations=READ_ONLY)
async def get_ssl_verification(zone_id: str) -> dict:
    """Get SSL/TLS certificate verification status/details for a zone."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}/ssl/verification")


@mcp.tool(annotations=READ_ONLY)
async def list_custom_certificates(zone_id: str) -> dict:
    """List custom (uploaded) SSL certificates for a zone."""
    client = get_client()
    return await client.request("GET", f"/zones/{zone_id}/custom_certificates")


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
async def list_origin_ca_certificates(zone_id: str | None = None) -> dict:
    """List Origin CA certificates, optionally filtered by zone."""
    client = get_client()
    params = {"zone_id": zone_id} if zone_id else {}
    return await client.request("GET", "/certificates", params=params)
