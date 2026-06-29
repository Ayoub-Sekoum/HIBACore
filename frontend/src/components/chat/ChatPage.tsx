import React from 'react';
import ChatContainer from './ChatContainer';
import { motion } from 'framer-motion';

/**
 * ChatPage
 * Pagina principale della chat, include il ChatContainer.
 * In questa vista l'agente può agire nel contesto HOBA Enterprise.
 */
const ChatPage: React.FC = () => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }}
      className="flex flex-col h-full w-full bg-[#f5f5f7] dark:bg-[#000]"
    >
      <div className="flex-1 flex flex-col h-full w-full relative">
        <ChatContainer />
      </div>
    </motion.div>
  );
};

export default ChatPage;
