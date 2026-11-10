const backend = 'uv run --project apps/backend';

export default {
  'apps/web/**/*.{ts,tsx}': ['eslint --fix', 'prettier --write'],
  '*.{js,mjs,cjs,json,md,yml,yaml,css,html}': 'prettier --write --ignore-unknown',
  'apps/backend/**/*.py': [`${backend} ruff check --fix`, `${backend} ruff format`],
};
