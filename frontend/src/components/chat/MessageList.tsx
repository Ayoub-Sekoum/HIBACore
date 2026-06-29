import React from 'react';
import { Message } from '../../types/chat';
import MessageBubble from './MessageBubble';

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="flex flex-col w-full pb-10">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </div>
  );
};

export default MessageList;
