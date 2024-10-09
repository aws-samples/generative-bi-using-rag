import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import dotenv from "dotenv";
import fs from "fs";
import path from "path";

// Load .env file
const envPath = path.resolve(__dirname, ".env");
if (fs.existsSync(envPath)) {
  dotenv.config({ path: `${envPath}.local` });
  dotenv.config({ path: envPath });
}

// https://vitejs.dev/config/
export default defineConfig({
  define: {
    "process.env": {
      VITE_TITLE: process.env.VITE_TITLE,
      VITE_LOGO: process.env.VITE_LOGO,
      VITE_RIGHT_LOGO: process.env.VITE_RIGHT_LOGO,
      VITE_LOGO_DISPLAY_ON_LOGIN_PAGE:
        process.env.VITE_LOGO_DISPLAY_ON_LOGIN_PAGE,
      VITE_COGNITO_REGION: process.env.VITE_COGNITO_REGION,
      VITE_COGNITO_USER_POOL_ID: process.env.VITE_COGNITO_USER_POOL_ID,
      VITE_COGNITO_USER_POOL_WEB_CLIENT_ID:
        process.env.VITE_COGNITO_USER_POOL_WEB_CLIENT_ID,
      VITE_COGNITO_IDENTITY_POOL_ID: process.env.VITE_COGNITO_IDENTITY_POOL_ID,
      VITE_SQL_DISPLAY: process.env.VITE_SQL_DISPLAY,
      VITE_BACKEND_URL: process.env.VITE_BACKEND_URL,
      VITE_WEBSOCKET_URL: process.env.VITE_WEBSOCKET_URL,
      VITE_LOGIN_TYPE: process.env.VITE_LOGIN_TYPE,
      VITE_APP_VERSION: process.env.VITE_APP_VERSION,
      VITE_USE_SSO_LOGIN: process.env.VITE_USE_SSO_LOGIN,
      VITE_SSO_FED_AUTH_PROVIDER: process.env.VITE_SSO_FED_AUTH_PROVIDER,
      VITE_SSO_OAUTH_DOMAIN: process.env.VITE_SSO_OAUTH_DOMAIN,
      VITE_OIDC_ISSUER: process.env.VITE_OIDC_ISSUER,
      VITE_OIDC_CLIENT_ID: process.env.VITE_OIDC_CLIENT_ID,
      VITE_OIDC_URL_LOGOUT: process.env.VITE_OIDC_URL_LOGOUT,
      VITE_OIDC_URL_REDIRECT: process.env.VITE_OIDC_URL_REDIRECT,
    },
  },
  plugins: [react()],
  server: {
    port: 3000,
  },
});
