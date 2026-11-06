import { mkdir, readFile, writeFile } from 'node:fs/promises';

await mkdir('dist', { recursive: true });
await writeFile('dist/index.html', await readFile('index.html'));
await writeFile('dist/404.html', '<!doctype html><title>Not found</title><h1>Not found</h1>');
const config = {
  url: process.env.SUPABASE_PUBLIC_URL || '',
  publicKey: process.env.SUPABASE_PUBLIC_KEY || '',
  release: process.env.HWSUPABASE_RELEASE || 'local',
};
// Only explicit public values enter the browser artifact.
await writeFile('dist/config.json', JSON.stringify(config));
