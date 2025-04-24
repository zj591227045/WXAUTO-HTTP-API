@router.post("/message/send-typing")
async def send_typing_text(
    request: Request,
    data: SendTypingTextRequest
):
    try:
        # Format message with @ mentions if at_list is provided
        message = data.message
        if data.at_list:
            # Add line break before @ mentions if message is not empty
            if message and not message.endswith('\n'):
                message += '\n'
            # Add @ mentions in correct format
            for user in data.at_list:
                message += f"{{@{user}}}"
                if user != data.at_list[-1]:  # Add line break between mentions
                    message += '\n'
        
        chat_window = await get_chat_window(data.who)
        if not chat_window:
            raise HTTPException(
                status_code=404,
                detail=f"Chat window not found for {data.who}"
            )
            
        chat_window.SendTypingText(message, clear=data.clear)
        return success_response()
        
    except Exception as e:
        return error_response(3001, f"发送失败: {str(e)}") 