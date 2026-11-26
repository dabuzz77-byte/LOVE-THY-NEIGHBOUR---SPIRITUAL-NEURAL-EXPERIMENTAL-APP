# -*- coding: utf-8 -*-
"""
1-0 TRUTH PARITY SPECIFICATION: PRODUCTION WSGI SERVER GATEWAY
Bridges localized control scripts into a hardened real-world runtime architecture.
"""

import sys
from app import app as native_transceiver_application

class ProductionWSGIAdapter:
    def __init__(self, application_instance):
        self.application = application_instance
        self.server_signature = "Sovereign-Transceiver-WSGI/2.0"

    def __call__(self, environ, start_response):
        # Enforce server-side connection parameter sanitization
        def production_headers_interceptor(status_string, response_headers, exc_info=None):
            secure_headers = list(response_headers)
            secure_headers.append(("Server", self.server_signature))
            secure_headers.append(("X-Content-Type-Options", "nosniff"))
            secure_headers.append(("X-Frame-Options", "DENY"))
            return start_response(status_string, secure_headers, exc_info)
            
        return self.application(environ, production_headers_interceptor)

# Expose the production container target mapping explicitly
production_gateway_target = ProductionWSGIAdapter(native_transceiver_application)

if __name__ == '__main__':
    try:
        from waitress import serve
        print("=== LAUNCHING REAL-WORLD ELEVATED SERVER RUNTIME ===")
        print("Binding structural pipelines to production network adapters on Port 8080...")
        serve(native_transceiver_application, host='0.0.0.0', port=8080, threads=8)
    except ModuleNotFoundError:
        print("[INFRASTRUCTURE ERROR]: Production runtime engine 'waitress' not located.")
        print("Please execute your automated stack provisioning script pass.")
        sys.exit(1)
