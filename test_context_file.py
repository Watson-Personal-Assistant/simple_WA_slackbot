from unittest import TestCase
from os.path import join, dirname
import json
import os


class TestContextFile(TestCase):
    def test_context_file(self):

        # Ensure .env file exists
        context_path = join(dirname(__file__), 'context.json')
        print("Context.json Path: " + str(context_path))

        context_file_exists = os.path.exists(context_path)
        print("Context file Exists: " + str(context_file_exists))

        self.assertTrue(context_file_exists)

    def test_context_json(self):
        context_path = join(dirname(__file__), 'context.json')

        # Load context from context.json file
        with open('context.json') as json_file:
            context = json.load(json_file)

        print("\n" + "Context:\n" + str(context) + "\n")

        # Ensure context.json contains valid JSON
        self.assertTrue(is_json(context))


def is_json(myjson):
    try:
        json_object = json.dumps(myjson)
    except ValueError:
        return False
    return True
