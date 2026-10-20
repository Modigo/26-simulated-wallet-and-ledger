/** @type {import('next').NextConfig} */
module.exports={async rewrites(){return[{source:"/api/:path*",destination:(process.env.BACKEND_INTERNAL_URL||"http://127.0.0.1:8000")+"/api/:path*"},{source:"/healthz",destination:(process.env.BACKEND_INTERNAL_URL||"http://127.0.0.1:8000")+"/health"}]}}
