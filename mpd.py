from lxml import etree
from operator import itemgetter

def parseMpd(mpd):
    mpd = mpd.replace('\\"', '"')
    mpd_xml = etree.fromstring(mpd)

    ns = {'mpd': "urn:mpeg:dash:schema:mpd:2011"}

    duration = mpd_xml.xpath("//mpd:Period/@duration", namespaces=ns)[0]
    duration = float(duration.replace('PT', '').replace('S', ''))

    video_reprs = []
    audio_reprs = []

    reprs_list = mpd_xml.xpath("//mpd:AdaptationSet/mpd:Representation", namespaces=ns)
    for representation in reprs_list:
        repr_item = {}
        repr_item['id'] = representation.xpath("@id", namespaces=ns)[0]
        repr_item['mimeType'] = representation.xpath("@mimeType", namespaces=ns)[0]
        repr_item['codecs'] = representation.xpath("@codecs", namespaces=ns)[0]
        repr_item['bandwidth'] = int(representation.xpath("@bandwidth", namespaces=ns)[0])
        repr_item['BaseURL'] = representation.xpath("mpd:BaseURL/text()", namespaces=ns)[0]
        if 'video' in repr_item['mimeType']:
            repr_item['width'] = int(representation.xpath("@width", namespaces=ns)[0])
            repr_item['height'] = int(representation.xpath("@height", namespaces=ns)[0])
            fr_temp = representation.xpath("@frameRate", namespaces=ns)[0].split('/')
            repr_item['frameRate'] = float(fr_temp[0]) / float(fr_temp[1])
            video_reprs.append(repr_item)
        elif 'audio' in repr_item['mimeType']:
            audio_reprs.append(repr_item)
        else:
            print('Unrecognized mimeType: ' + repr_item['mimeType'])

    video_reprs.sort(key=itemgetter('bandwidth'))
    audio_reprs.sort(key=itemgetter('bandwidth'))

    return video_reprs, audio_reprs