import StringIO
import json
import logging
import random
import urllib
import urllib2
import os
import re

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

import time

# telegram
#from telegram import ReplyKeyboardMarkup

TOKEN = os.environ.get('TOKEN')

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'


# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)

# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False


# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib2.urlencode({'url': url})))))

class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        callback_data = None
        callback_query_id = None

        update_id = body['update_id']

        if 'message' in body:
            message = body['message']
        elif 'edited_message' in body:
            message = body['edited_message']
        elif 'callback_query' in body:
            callback_query = body['callback_query']
            callback_data = callback_query.get('data')
            callback_query_id = callback_query.get('id')
            message = callback_query.get('message')
            
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

        # Find quantity in text
        regexp = re.compile(r'[0-9]{2,4}')

        if not text:
            logging.info('no text')
            return

        def sendMessage(msg=None,reply_keyboard=None,reply_to=False):
            data = {
                'chat_id': str(chat_id),
                'disable_web_page_preview': 'true',
                'parse_mode': 'Markdown'
            }
            if msg:
                data['text'] = msg
            if reply_keyboard:
                data['reply_markup'] = json.dumps(reply_keyboard)
            if reply_to:
                data['reply_to_message_id']= str(message_id)

            data_formatted = json.dumps(data)
            req = urllib2.Request(BASE_URL + 'sendMessage', data_formatted, {'Content-Type': 'application/json'})
            f = urllib2.urlopen(req, timeout=4)
            resp = f.read()
            f.close()

            logging.info('sendMessage send response:')
            logging.info(resp)

            return

        def editMessage(message_id, text):
            data = {
                'chat_id': str(chat_id),
                'message_id': message_id,
                'text': text,
                'disable_web_page_preview': 'true',
                'parse_mode': 'Markdown'
            }

            data_formatted = json.dumps(data)
            req = urllib2.Request(BASE_URL + 'editMessageText', data_formatted, {'Content-Type': 'application/json'})
            f = urllib2.urlopen(req, timeout=4)
            resp = f.read()
            f.close()

            logging.info('editMessage send response:')
            logging.info(resp)

            return

        def answerCallbackQuery(query_id=None):
            if query_id:
                data = {
                    'callback_query_id': str(query_id),
                    'text': 'Callback successful'
                }
                data_formatted = json.dumps(data)
                req = urllib2.Request(BASE_URL + 'answerCallbackQuery', data_formatted, {'Content-Type': 'application/json'})
                f = urllib2.urlopen(req, timeout=4)
                resp = f.read()
                f.close()
            else:
                resp='No callback_query_id was set'

            logging.info('answerCallbackQuery send response:')
            logging.info(resp)
            return

        def brew():
            msg = ('Choose a recipe below')
            reply_keyboard = {'inline_keyboard':[[{'text':"4:6","callback_data": "recipe_4_6"}]],'one_time_keyboard':True}
            sendMessage(msg=msg, reply_keyboard=reply_keyboard,reply_to=True)

        def brewGuide(recipe):
            if recipe == "brew_4_6":
                for i in range(1,6):
                    o = 5
                    while o > 0:
                        editMessage(message_id=message_id,text="*Pour no. {}* \n\nStarting in {}".format(i,o))
                        time.sleep(1)
                        o -= 1
                    p = 45
                    while p > 5:
                        if i < 5:
                            editMessage(message_id=message_id,text='*Pour no. {}* \n\nGO! ({} until pour no. {})'.format(i, p, i+1))
                        else:
                            editMessage(message_id=message_id,text='*Pour no. {}* \n\nGO! ({} until last pour)'.format(i, p))
                        time.sleep(1)
                        p -= 1
                editMessage(message_id=message_id,text='Congratulations, all done!')
                return
            return

        if text.startswith('/'):
            if text == '/start':
                reply_keyboard = {'keyboard':[[{'text':"/brew"},{'text':"/stop"}]],'one_time_keyboard':True}
                sendMessage(msg=("SLURP brew bot enabled. I'm still a work in progress, so be gentle.\nSelect an action below."),reply_keyboard=reply_keyboard,reply_to=True)
                setEnabled(chat_id, True)
            elif text == '/stop':
                sendMessage('SLURP brew bot disabled')
                setEnabled(chat_id, False)
            elif text == '/brew':
                sendMessage("Cool, let's brew!")
                brew()
            else:
                sendMessage('What command?')
        elif callback_data == 'recipe_4_6':
            callback_data = None
            answerCallbackQuery(callback_query_id)
            reply_keyboard = {'keyboard':[[{'text':"15g"},{'text':"20g"},{'text':"25g"},{'text':"30g"}]],'one_time_keyboard':True}
            sendMessage('How much coffee are you using? (Amount of coffee as XX g.)', reply_keyboard=reply_keyboard)
        elif callback_data == 'brew_4_6':
            callback_data = None
            answerCallbackQuery(callback_query_id)
            brewGuide("brew_4_6")
        elif regexp.search(text):
            quantityMatch = re.match(r'[0-9]{2,4}', text)
            quantity = int(quantityMatch.group(0))
            pour = quantity*3
            finalquantity = pour*5
            sendMessage("*Here's the recipe:*" + "\n- The target weight is {}g".format(finalquantity) + "\n- One pour is {}g every 45 s".format(pour) + "\n- 5 pours in total" + "\n- The amount of coffee to grind is {}g".format(quantity) + "\n\n_Enjoy!_",reply_to=True)
            reply_keyboard = {'inline_keyboard':[[{'text':"Start brewing\n(5s countdown)","callback_data": "brew_4_6"}]],'one_time_keyboard':True}
            sendMessage(msg='Do you want to brew now?', reply_keyboard=reply_keyboard)
        else:
            if getEnabled(chat_id):
                sendMessage('I got your message, but I do not know how to answer...')
            else:
                logging.info('not enabled for chat_id {}'.format(chat_id))


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
