import type { NextApiRequest, NextApiResponse } from 'next';
import { execSync } from 'child_process';
import path from 'path';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const scriptPath = path.join(process.cwd(), 'scripts', 'organizations.py');

  try {
    if (req.method === 'GET') {
      const output = execSync(`python ${scriptPath} list`, {
        env: process.env,
        encoding: 'utf-8',
      });
      const data = JSON.parse(output);
      res.status(200).json(data);
    } else if (req.method === 'POST') {
      const { name } = req.body;
      if (!name) {
        return res.status(400).json({ error: 'Organization name is required' });
      }
      const output = execSync(`python ${scriptPath} create "${name}"`, {
        env: process.env,
        encoding: 'utf-8',
      });
      const data = JSON.parse(output);
      res.status(201).json(data);
    } else {
      res.status(405).json({ error: 'Method not allowed' });
    }
  } catch (error: any) {
    console.error('Error executing Python script:', error);
    res.status(500).json({ error: error.message || 'Internal server error' });
  }
}
