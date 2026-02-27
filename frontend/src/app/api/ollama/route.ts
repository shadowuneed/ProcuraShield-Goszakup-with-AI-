import { NextRequest, NextResponse } from 'next/server';

const OLLAMA_URL = 'http://localhost:11434';
const DEFAULT_MODEL = 'llama3:latest';

export async function POST(req: NextRequest) {
  try {
    const { prompt, model } = await req.json();
    if (!prompt) return NextResponse.json({ error: 'No prompt' }, { status: 400 });

    const res = await fetch(`${OLLAMA_URL}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: model ?? DEFAULT_MODEL,
        prompt,
        stream: false,
        options: { temperature: 0.2, num_predict: 2048 },
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      return NextResponse.json({ error: `Ollama error: ${err}` }, { status: 502 });
    }

    const data = await res.json();
    const text: string = data.response ?? '';

    if (!text) return NextResponse.json({ error: 'Empty response from Ollama' }, { status: 502 });

    return NextResponse.json({ text, model: model ?? DEFAULT_MODEL });
  } catch (e) {
    return NextResponse.json({ error: `Connection failed: ${String(e)}` }, { status: 500 });
  }
}

export async function GET() {
  try {
    const res = await fetch(`${OLLAMA_URL}/api/tags`);
    const data = await res.json();
    return NextResponse.json({ models: data.models ?? [] });
  } catch {
    return NextResponse.json({ models: [] });
  }
}
