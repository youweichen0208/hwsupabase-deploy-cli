import os

from .core import DeliveryError, read_document


def make_client(config, factory=None):
    if factory is None:
        try:
            from obs import ObsClient
        except ImportError:
            raise DeliveryError("Install the optional obs extra for structured OBS probes") from None
        factory = ObsClient
    profile = config.data["obs"]
    ak = os.environ.get(profile.get("access_key_env", "HWC_OBS_ACCESS_KEY"))
    sk = os.environ.get(profile.get("secret_key_env", "HWC_OBS_SECRET_KEY"))
    token = os.environ.get(profile.get("token_env", "HWC_OBS_SECURITY_TOKEN"))
    if not ak or not sk:
        raise DeliveryError("Provide scoped OBS credentials in the configured environment variables")
    return factory(access_key_id=ak, secret_access_key=sk, security_token=token, server=profile["endpoint"])


def probe(config, call, factory=None):
    bucket = call.get("bucket")
    if bucket not in {config.data["obs"].get(k) for k in ("site_bucket", "artifact_bucket", "storage_bucket")} or not bucket:
        raise DeliveryError("OBS probe bucket is outside this customer's configuration")
    client = make_client(config, factory)
    try:
        target = call["target"]
        if target == "object":
            response = client.getObjectMetadata(bucket, call["key"])
        else:
            response = getattr(client, {"bucket": "getBucketMetadata", "website": "getBucketWebsite", "cors": "getBucketCors"}[target])(bucket)
        # Only explicit absence is recoverable. A 403 must never lead to creation.
        if response.status == 404:
            return {"exists": False}
        if not 200 <= response.status < 300:
            raise DeliveryError("OBS probe failed; check endpoint, identity and permissions")
        result = {"exists": True}
        if target == "object":
            result.update({"etag": str(response.body.etag).strip('"'), "size": response.body.contentLength,
                           "content_type": response.body.contentType})
        return result
    except DeliveryError:
        raise
    except Exception:
        raise DeliveryError("Official OBS SDK probe failed") from None
    finally:
        client.close()


def configure_site(config, path, factory=None):
    """Optional official SDK fallback for capabilities absent from obsutil."""
    settings = read_document(path)
    if set(settings) - {"website", "cors"}:
        raise DeliveryError("OBS site settings only support website and cors")
    profile = config.data["obs"]
    bucket = profile.get("site_bucket")
    if not bucket:
        raise DeliveryError("Site bucket is not configured")
    client = make_client(config, factory)
    try:
        for key, method in (("website", "setBucketWebsite"), ("cors", "setBucketCors")):
            if key in settings:
                response = getattr(client, method)(bucket, settings[key])
                if not 200 <= response.status < 300:
                    raise DeliveryError("OBS " + key + " configuration failed; check scoped permissions")
        # Readback available as separate step, never equate 2xx config to browser validation.
        for key, method in (("website", "getBucketWebsite"), ("cors", "getBucketCors")):
            if key in settings and not 200 <= getattr(client, method)(bucket).status < 300:
                raise DeliveryError("OBS configuration readback failed")
    except DeliveryError:
        raise
    except Exception:
        raise DeliveryError("Official OBS SDK operation failed; inspect redacted diagnostics") from None
    finally:
        client.close()
    return {"bucket": bucket, "configured": sorted(settings), "browser_verified": False}
