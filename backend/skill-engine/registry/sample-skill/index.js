module.exports = async function(payload) {
  return {
    success: true,
    message: `Hello! You sent: ${payload.text || 'nothing'}`,
    timestamp: new Date().toISOString()
  };
};