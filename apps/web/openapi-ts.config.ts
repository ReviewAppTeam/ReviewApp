import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: '../backend/openapi.json',
  output: 'src/api/generated',
  plugins: [
    { name: '@hey-api/client-fetch', runtimeConfigPath: './src/api/client-config.ts' },
    'zod',
    { name: '@hey-api/sdk', validator: true },
    '@tanstack/react-query',
  ],
});
