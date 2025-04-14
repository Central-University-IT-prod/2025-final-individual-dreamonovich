from django.utils.encoding import filepath_to_uri
from storages.backends.s3 import S3Storage


class CustomS3Storage(S3Storage):
    def url(self, name, headers=None, response_headers=None, expire=None):
        name = self._normalize_name(self._clean_name(name))
        if self.custom_domain:
            return "%s//%s/%s" % (
                self.url_protocol,
                self.custom_domain,
                filepath_to_uri(name),
            )

        if expire is None:
            expire = self.querystring_expire

        return self.connection.generate_url(
            expire,
            method="GET",
            bucket=self.bucket.name,
            key=self._encode_name(name),
            headers=headers,
            query_auth=self.querystring_auth,
            force_http=not self.secure_urls,
            response_headers=response_headers,
        )
