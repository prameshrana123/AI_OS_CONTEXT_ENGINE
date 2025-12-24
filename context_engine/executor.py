import webbrowser
import pyperclip
import platform
import os

ALLOWED_ACTIONS = {
    "notify_user",
    "open_browser",
    "copy_to_clipboard",
    "none"
}

class ActionExecutor:
    """
    Safely executes actions proposed by the AI.
    Strictly validates actions against ALLOWED_ACTIONS.
    """
    
    @staticmethod
    def execute(proposal_dict):
        """
        Executes the proposed action if it is allowed.
        
        Args:
            proposal_dict (dict): The proposal dictionary containing 'action' and 'reason'.
            
        Returns:
            bool: True if executed successfully, False otherwise.
        """
        if not isinstance(proposal_dict, dict):
            print(f"❌ Executor: Invalid proposal format: {type(proposal_dict)}")
            return False

        action = proposal_dict.get("action")
        
        if isinstance(action, str):
            action = action.strip().lower()

        if action not in ALLOWED_ACTIONS:
            print(f"⚠️ Executor: Action '{action}' is NOT allowed. Blocked.")
            return False
            
        if action == "none":
            return True # No action needed, effectively a success
            
        print(f"⚙️ Executor: Executing safe action: {action}")
        
        try:
            if action == "open_browser":
                return ActionExecutor._handle_open_browser(proposal_dict)
            elif action == "copy_to_clipboard":
                return ActionExecutor._handle_copy_to_clipboard(proposal_dict)
            elif action == "notify_user":
                return ActionExecutor._handle_notify_user(proposal_dict)
        except Exception as e:
            print(f"❌ Executor: Error executing {action}: {e}")
            return False
            
        return False

    @staticmethod
    def _handle_open_browser(details):
        # In a real scenario, the LLM might provide a URL in the proposal.
        # For safety, we might want to default to a search if no URL is present,
        # or require a 'payload' field.
        # For now, we'll assume the LLM might put extra details in the dict,
        # but let's be safe and just open a default or safe URL if missing.
        
        # NOTE: The current prompt in ai.py doesn't explicitly ask for 'payload' or 'url'.
        # We might need to update the prompt if we want dynamic parameters.
        # For this iteration, we will just open a related search if possible, or a default.
        
        url = details.get("url")
        if not url:
             # Basic fallback behavior
             url = "https://www.google.com"
        
        webbrowser.open(url)
        return True

    @staticmethod
    def _handle_copy_to_clipboard(details):
        content = details.get("content")
        if not content:
            # If the LLM didn't specify content (it strictly follows the schem currently),
            # we might copy the 'reason' or just the 'insight'.
            # Let's copy the reason as a fallback.
            content = details.get("reason", "")
        
        pyperclip.copy(content)
        print(f"📋 Copied to clipboard: {content[:50]}...")
        return True

    @staticmethod
    def _handle_notify_user(details):
        message = details.get("reason", "Notification from AI Agent")
        print(f"\n🔔 NOTIFICATION: {message}\n")
        # In a GUI app, we would show a toast/popup here.
        return True
