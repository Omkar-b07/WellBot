from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from sqlalchemy import create_engine, text
import os

class ActionQueryKnowledgeBase(Action):

    def __init__(self):
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'InfyWellBot', 'project.db')
        self.db_engine = create_engine(f'sqlite:///{os.path.abspath(db_path)}')
        print(f"Action server connected to DB at: {os.path.abspath(db_path)}")

    def name(self) -> Text:
        return "action_query_knowledge_base"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        print("\n--- ACTION SERVER RECEIVED ---")
        latest_intent = tracker.latest_message['intent'].get('name')
        entities = tracker.latest_message.get('entities', [])
        metadata = tracker.latest_message.get('metadata') # Get metadata from Flask
        print(f"Detected Intent: {latest_intent}")
        print(f"Detected Entities: {entities}")
        print(f"Received Metadata: {metadata}")

        entity_value = next((e['value'] for e in entities if e['entity'] == 'condition'), None)
        print(f"Extracted Condition Entity: {entity_value}")

        # --- GET LANGUAGE FROM METADATA ---
        user_language = metadata.get('user_language', 'en') if metadata else 'en'
        # Basic validation, default to 'en'
        if user_language not in ['en', 'hi']:
            user_language = 'en'
        response_column = f"response_{user_language}" # 'response_en' or 'response_hi'
        print(f"Using language column: {response_column}")
        # --- END GET LANGUAGE ---

        valid_intent = None
        # --- FIX: ADD 'ask_prevention' TO THIS LIST ---
        if latest_intent in ['ask_symptom', 'ask_first_aid', 'ask_wellness_tip', 'ask_prevention']:
            valid_intent = latest_intent
        elif entity_value and latest_intent == 'inform':
            # ... (history lookup logic remains the same) ...
            for event in reversed(tracker.events):
                    if event.get('event') == 'user':
                        prev_intent = event.get('parse_data', {}).get('intent', {}).get('name')
                        # --- FIX: ADD 'ask_prevention' TO THIS LIST ---
                        if prev_intent in ['ask_symptom', 'ask_first_aid', 'ask_wellness_tip', 'ask_prevention']:
                            valid_intent = prev_intent
                            print(f"Found previous relevant intent: {valid_intent}")
                            break
            if not valid_intent:
                    valid_intent = 'ask_wellness_tip'
                    print(f"Defaulting 'inform' intent to: {valid_intent}")

        print(f"Final Valid Intent for DB Query: {valid_intent}")

        if not entity_value:
             # ... (missing entity logic remains the same) ...
             # --- FIX: ADD 'ask_prevention' TO THIS LIST ---
             if latest_intent in ['ask_symptom', 'ask_first_aid', 'ask_wellness_tip', 'inform', 'ask_prevention']:
                    dispatcher.utter_message(response="utter_ask_condition")
                    return []
             else:
                    dispatcher.utter_message(response="utter_not_found")
                    return []

        response_text = None
        if valid_intent:
            try:
                with self.db_engine.connect() as conn:
                    # --- USE CORRECT LANGUAGE COLUMN ---
                    query = text(f"SELECT {response_column} FROM health_knowledge WHERE intent = :i AND entity = :e")
                    # --- END USE CORRECT LANGUAGE ---
                    result = conn.execute(query, {"i": valid_intent, "e": entity_value.lower()}).fetchone()

                    if result and result[0]:
                        response_text = result[0]
                        print(f"Found DB entry for intent='{valid_intent}', entity='{entity_value}', lang='{user_language}'")
                    else:
                        # ... (fallback logic remains the same, but uses response_column) ...
                        print(f"DB entry not found for intent='{valid_intent}', lang='{user_language}'. Falling back...")
                        fallback_intent = 'ask_wellness_tip'
                        if valid_intent != fallback_intent:
                                query_fallback = text(f"SELECT {response_column} FROM health_knowledge WHERE intent = :i AND entity = :e LIMIT 1")
                                result_fallback = conn.execute(query_fallback, {"i": fallback_intent, "e": entity_value.lower()}).fetchone()
                                if result_fallback and result_fallback[0]:
                                    response_text = result_fallback[0]
                                    print(f"Found fallback DB entry for intent='{fallback_intent}', entity='{entity_value}', lang='{user_language}'")
                        
                        # If still no response_text, use the default for the intent
                        if not response_text:
                            print(f"No specific entry for {entity_value}, trying default for intent {valid_intent}")
                            query_default = text(f"SELECT {response_column} FROM health_knowledge WHERE intent = :i AND entity = 'default' LIMIT 1")
                            result_default = conn.execute(query_default, {"i": valid_intent}).fetchone()
                            if result_default and result_default[0]:
                                response_text = result_default[0]

            except Exception as e:
                print(f"!!! Database error: {e}")
                response_text = "Sorry, I encountered a database problem."

        if response_text:
            print(f"Sending reply (lang={user_language}): {response_text}")
            dispatcher.utter_message(text=response_text)
        elif valid_intent:
             print(f"No DB entry found for entity='{entity_value}' for intent='{valid_intent}' or fallback (lang={user_language}).")
             dispatcher.utter_message(response="utter_not_found")
        else:
             print("Have entity but no valid intent determined.")
             dispatcher.utter_message(text=f"I have information about '{entity_value}', but I'm not sure what you want to know. You can ask about symptoms, first aid, or wellness tips.")

        return []