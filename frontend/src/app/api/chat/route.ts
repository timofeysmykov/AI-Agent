import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message } = body;

    if (!message) {
      return NextResponse.json(
        { error: 'Сообщение не может быть пустым' },
        { status: 400 }
      );
    }

    // Вызываем Python скрипт для обработки запроса
    const { stdout, stderr } = await execAsync(
      `python -c "from ai_assistant.ai_agent import ClaudeAgentCore; import asyncio, os, json, dotenv; dotenv.load_dotenv(); agent = ClaudeAgentCore(claude_api_key=os.getenv('CLAUDE_API_KEY')); result = asyncio.run(agent.process_query('${message.replace(/'/g, "\\'")}'));  print(json.dumps({'response': result, 'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'}))"`,
      { maxBuffer: 1024 * 1024 * 10 } // 10MB buffer
    );

    if (stderr) {
      console.error('Ошибка при выполнении Python скрипта:', stderr);
      return NextResponse.json(
        { error: 'Ошибка при обработке запроса' },
        { status: 500 }
      );
    }

    const result = JSON.parse(stdout.trim());
    
    return NextResponse.json({
      response: result.response,
      timestamp: result.timestamp
    });
  } catch (error) {
    console.error('Ошибка при обработке запроса:', error);
    return NextResponse.json(
      { error: 'Внутренняя ошибка сервера' },
      { status: 500 }
    );
  }
} 