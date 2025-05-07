export const validateEmail = (email) => {
  // Basic email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  // Check if it's a valid email format
  if (!emailRegex.test(email)) {
    return false;
  }
  
  // Check if it's an MSOE email (ends with msoe.edu)
  return email.toLowerCase().endsWith('msoe.edu');
  
};
