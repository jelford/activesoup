
def resolve(raw_response):
    return JsonResponse(raw_response)


class JsonResponse:

    def __init__(self, raw_response):
        self.raw_response = raw_response
        self.json = raw_response.json()

    def __getitem__(self, name):
        return self.json[name]
