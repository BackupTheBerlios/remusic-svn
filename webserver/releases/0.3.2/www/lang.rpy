# -*- mode: python -*-

import twisted.web.util

class LangSwitch(twisted.web.util.Redirect):

    def __init__(self):
        twisted.web.util.Redirect.__init__(self, "/")
        
    def render(self, request):
        import remus.i18n
        sess = request.getSession(remus.i18n.ITranslator)
        # Check if user want to change language
        if request.args.has_key("lang"):
            sess.setLanguage(request.args["lang"][0])

        self.url = request.getHeader("referer") or self.url
        return twisted.web.util.Redirect.render(self, request)
        

resource = LangSwitch()
