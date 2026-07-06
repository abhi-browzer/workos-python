import { useState, useEffect } from 'react';
import Head from 'next/head';

interface Organization {
  id: string;
  name: string;
  created_at: string;
}

interface User {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
}

export default function Home() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [newOrgName, setNewOrgName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchOrganizations();
    fetchUsers();
  }, []);

  const fetchOrganizations = async () => {
    try {
      const res = await fetch('/api/organizations');
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setOrganizations(data.organizations || []);
      }
    } catch (err) {
      setError('Failed to fetch organizations');
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await fetch('/api/users');
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setUsers(data.users || []);
      }
    } catch (err) {
      setError('Failed to fetch users');
    }
  };

  const createOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/organizations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newOrgName }),
      });
      const data = await res.json();

      if (data.error) {
        setError(data.error);
      } else {
        setNewOrgName('');
        fetchOrganizations();
      }
    } catch (err) {
      setError('Failed to create organization');
    } finally {
      setLoading(false);
    }
  };

  const getAuthUrl = async () => {
    try {
      const res = await fetch('/api/auth/url');
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else if (data.error) {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to get auth URL');
    }
  };

  return (
    <>
      <Head>
        <title>WorkOS Python + Next.js Example</title>
        <meta name="description" content="WorkOS integration example" />
      </Head>

      <main style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem' }}>
        <h1>WorkOS Python + Next.js Example</h1>

        {error && (
          <div style={{ padding: '1rem', background: '#fee', border: '1px solid #c00', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <section style={{ marginBottom: '2rem' }}>
          <h2>Authentication</h2>
          <button onClick={getAuthUrl} style={{ padding: '0.5rem 1rem', cursor: 'pointer' }}>
            Get SSO Authorization URL
          </button>
        </section>

        <section style={{ marginBottom: '2rem' }}>
          <h2>Organizations ({organizations.length})</h2>
          <form onSubmit={createOrganization} style={{ marginBottom: '1rem' }}>
            <input
              type="text"
              value={newOrgName}
              onChange={(e) => setNewOrgName(e.target.value)}
              placeholder="New organization name"
              style={{ padding: '0.5rem', marginRight: '0.5rem', width: '250px' }}
            />
            <button type="submit" disabled={loading} style={{ padding: '0.5rem 1rem', cursor: 'pointer' }}>
              {loading ? 'Creating...' : 'Create Organization'}
            </button>
          </form>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {organizations.map((org) => (
              <li key={org.id} style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                <strong>{org.name}</strong>
                <br />
                <small>ID: {org.id}</small>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2>Users ({users.length})</h2>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {users.map((user) => (
              <li key={user.id} style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>
                <strong>{user.email}</strong>
                {(user.first_name || user.last_name) && (
                  <>
                    {' '}- {user.first_name} {user.last_name}
                  </>
                )}
                <br />
                <small>ID: {user.id}</small>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </>
  );
}
