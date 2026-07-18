import type { NextApiRequest, NextApiResponse } from 'next';
import { execSync } from 'child_process';
import path from 'path';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const scriptPath = path.join(process.cwd(), 'scripts', 'users.py');

  try {
    const output = execSync(`python ${scriptPath}`, {
      env: process.env,
      encoding: 'utf-8',
    });
    const data = JSON.parse(output);
    res.status(200).json(data);
  } catch (error: any) {
    console.error('Error executing Python script:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
  }
}
