import { defineConfig } from 'vite';
const csp = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
export default defineConfig(({ command }) => ({
  base: process.env.BASE_PATH || '/lidcheck/',
  plugins: [{name:'privacy-csp', transformIndexHtml(html) {
    return command === 'build' ? html.replace('<!-- CSP -->', `<meta http-equiv="Content-Security-Policy" content="${csp}">`) : html;
  }}]
}));
