import vim
import openai
import os

# Set your OpenAI API key here or load from environment
openai.api_key = vim.eval('get(g:, "vim_pilot_openai_api_key", "")') or os.getenv('OPENAI_API_KEY')


def open_chat():
    # Open a new split window for chat
    vim.command('botright new')
    vim.command('setlocal buftype=nofile')
    vim.command('setlocal bufhidden=wipe')
    vim.command('setlocal nobuflisted')
    vim.command('setlocal noswapfile')
    vim.command('setlocal nonumber')
    vim.command('setlocal norelativenumber')
    vim.command('setlocal wrap')
    vim.command('setlocal modifiable')
    vim.current.buffer[:] = ["VimPilot Chat - Type your prompt below:", "-------------------------------------", "", "> "]
    vim.command('normal! G$')
    
    # Wait for user input (simulate for now)
    # In a real plugin, you'd use a loop or async input
    prompt = vim.eval('input("VimPilot> ")')
    if not prompt.strip():
        vim.current.buffer.append(["(No input provided)"])
        return
    
    # Call OpenAI API
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response['choices'][0]['message']['content']
    except Exception as e:
        reply = f"[Error from OpenAI: {e}]"
    
    # Display response
    vim.current.buffer.append(["> " + prompt, "AI: " + reply, "", "> "])
    vim.command('normal! G$') 