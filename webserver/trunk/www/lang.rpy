# -*- mode: python -*-

import twisted.web.util

class LangSwitch(twisted.web.util.Redirect):

    def __init__(self):
        twisted.web.util.Redirect.__init__(self, "/")
        
    def render(self, request):
        import remus.i18n
        # Check if user want to change language
        if request.args.has_key("lang"):
            remus.i18n.install(request.args["lang"][0])

        self.url = request.getHeader("referer") or self.url
        return twisted.web.util.Redirect.render(self, request)
        

resource = LangSwitch()
