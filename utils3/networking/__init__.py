import requests


class Session:
    def __init__(self, headers=None):
        self.session = requests.Session()
        self.headers = headers

    def injectCookie(self, name, value):
        self.session.cookies.set(name=name, value=value)

    def downloadFile(self, url, filename, callback):
        """
        :param url: The URL to download from
        :param filename: The filename to save the file as
        :param callback: A function to call with the current progress, will receive the current percentage as a
                        parameter. callback is not threaded.
        :return:
        """
        percentage_done = 0
        size_of_file = 0
        with self.session.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        percentage_done += len(chunk)
                        if size_of_file == 0:
                            size_of_file = int(r.headers['Content-Length'])

                        callback(percentage_done / size_of_file)

        callback(1)


    def get(self, url, *args, **kwargs):
        return self.session.get(url, *args, **kwargs, headers=self.headers)

    def post(self, url, *args, **kwargs):
        return self.session.post(url, *args, **kwargs, headers=self.headers)

    def put(self, url, *args, **kwargs):
        return self.session.put(url, *args, **kwargs, headers=self.headers)
