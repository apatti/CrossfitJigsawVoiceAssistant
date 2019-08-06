import json
import logging
from bs4 import BeautifulSoup
import requests
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

url="https://www.crossfitjigsaw.com/workout-blog"
alexa_card_title=""
alexa_card_content=""

def lambda_handler(event, context):
    
    if "session" in event and "application" in event["session"]:
        if (event['session']['application']['applicationId'] !=
        "AMAZON SKILL ID"):
            raise ValueError("Invalid Application ID")
        else:
            response = handleAlexaSkill(event)
    else:
        response = handleGoogleAction()
    #if "originalDetectIntentRequest" in event:
    #    if "source" in event["originalDetectIntentRequest"]:
    #        if event["originalDetectIntentRequest"]["source"]!="google":
    #            raise ValueError("Invalid source")
        #response = handleGoogleAction()
    
    return response

def handleAlexaSkill(event):
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

    pass

def handleGoogleAction():
    response = {}
    response['fulfillmentText']="Crossfit jigsaw"
    #response['payload']={"google":{}}
    google = {}
    google['expectUserResponse']=False
    google['richResponse']={
        'items':[
            {"simpleResponse":
                {"textToSpeech":formulateWorkoutSpeech()}
            }]}
    response['payload']={"google":google}
    # TODO implement
    return response

def formulateWorkoutSpeech(date=None):
    global alexa_card_content,alexa_card_title
    workout = getWorkout()
    if workout is None:
        alexa_card_title="Workout information is not available"
        return "<speak>Workout information is not available</speak>"
    
    workout_date_search = re.search('\d\d/\d\d/\d\d\d\d',workout[0])
    if workout_date_search is not None:
        workout_date = workout_date_search.group()
    else:
        workout_date = None

    #handle none workout_date
    speech = "<speak>The workout for <say-as interpret-as='date' format='md' >{}</say-as> is as follows <p>".format(workout_date)
    alexa_card_title="The workout for {} is as follows".format(workout_date)
    for item in workout[1:]:
        gender_weight_search = re.search('(\d+)#/(\d+)#',item)
        if gender_weight_search is not None:
            m_weight=gender_weight_search.group(1)
            w_weight=gender_weight_search.group(2)
            item = item.replace(gender_weight_search.group(),
                    "men {} pounds and ladies {} pounds".format(m_weight,w_weight))
        
        reps_search = re.search(' x (\d+)',item)
        if reps_search is not None:
            rep_count = reps_search.group(1)
            item = item.replace(reps_search.group(),' repeat {} times'.format(rep_count))
            
        if '/' in item:
            item = item.replace('/',' or ')
            
        speech += "<break time='1s'/><s>{}</s>".format(item)
        alexa_card_content +="{}\n".format(item)
    speech +="</p></speak>"
    
    #print(speech)
    return speech
    

def getWorkout(date=None):
    page = requests.get(url)
    content = BeautifulSoup(page.content, 'html.parser')
    workout_block = content.select('.sqs-block.html-block.sqs-block-html')[1]
    items = workout_block.findAll('p')
    workoutStartIndex=-1
    workout=[]
    for i in range(0,len(items)):
        if 'Workout' not in items[i].getText() and workoutStartIndex==-1:
            continue
        else:
            workoutStartIndex=i
        workout.append(items[i].getText())
    if workoutStartIndex==-1:
        return None
    
    return workout
    
def build_speechlet_response(title, output,card_title,card_content, reprompt_text, should_end_session):
    
    #output = "<speak>{}</speak>".format(output)
    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': output
        },
        'card': {
            'type': 'Simple',
            'title': card_title,
            'content': card_content
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "<speak>Welcome to the Crossfit Jigsaw skill.<break time='500ms'/>" \
                    "I can give you the workout details</speak>"
    card_content = "Welcome to the Crossfit Jigsaw skill.\nI can give you the workout details."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "You can check for workout by saying, " \
                    "What's the new workout"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output,card_title,card_content, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "<speak>Thank you for trying Crossfit Jigsaw skill." \
                    "Have a nice day!</speak>"
    card_content = "Thank you for trying Crossfit Jigsaw skill.\nHave a nice day!"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, card_title,card_content,None, should_end_session))

def get_workout_intent(intent,session):
    global alexa_card_content,alexa_card_title
    session_attributes={}
    reprompt_text=None
    
    speech_output = formulateWorkoutSpeech()
    return build_response(session_attributes, build_speechlet_response(
        alexa_card_title, speech_output,alexa_card_title,alexa_card_content, reprompt_text, True))

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name.lower() == "whatisthenewworkout":
        return get_workout_intent(intent,session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    
    # add cleanup logic here

