// src/api/client.js
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {}

export async function apiGet(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    throw new ApiError(`${res.status} ${res.statusText}`);
  }
  return res.json();
}

export { BASE_URL };
