import json
from dateutil.parser import parse

from rdflib import Literal, BNode
from rdflib.namespace import Namespace

from ckanext.dcat.profiles import (
    GSP,
    DCAT,
    DCT,
    FOAF,
    VCARD,
    RDF,
    RDFS,
    XSD,
)

QUDT = Namespace('https://qudt.org/schema/qudt/')
VRA = Namespace('https://www.loc.gov/standards/vracore/vra.xsd')

from .base import namespaces

namespaces.update(dict(qudt=QUDT, vra=VRA))

from ckanext.dcat.utils import resource_uri

from .base import URIRefOrLiteral, CleanedURIRef
from .euro_dcat_ap_3 import EuropeanDCATAP3Profile


class PresencasDCATAP3Profile(EuropeanDCATAP3Profile):
    """
    Perfil RDF baseado no padrão europeu do DCAT 3, com adições de campos dos datasets do Projeto Presenças.
    """

    def parse_dataset(self, dataset_dict, dataset_ref):

        # Call base method for common properties
        dataset_dict = self._parse_dataset_base(dataset_dict, dataset_ref)

        # DCAT AP v2 properties also applied to higher versions
        dataset_dict = self._parse_dataset_v2(dataset_dict, dataset_ref)

        # DCAT AP v2 scheming fields
        dataset_dict = self._parse_dataset_v2_scheming(dataset_dict, dataset_ref)

        self._parse_dataset_v3_presencas(dataset_dict, dataset_ref)

        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):

        # Call base method for common properties
        self._graph_from_dataset_base(dataset_dict, dataset_ref)

        # DCAT AP v2 properties also applied to higher versions
        self._graph_from_dataset_v2(dataset_dict, dataset_ref)

        # DCAT AP v2 scheming fields
        self._graph_from_dataset_v2_scheming(dataset_dict, dataset_ref)

        # DCAT AP v3 properties also applied to higher versions
        self._graph_from_dataset_v3(dataset_dict, dataset_ref)

        self._graph_from_dataset_v3_presencas(dataset_dict, dataset_ref)

    def graph_from_catalog(self, catalog_dict, catalog_ref):

        self._graph_from_catalog_base(catalog_dict, catalog_ref)

    def _parse_dataset_v3_presencas(self, dataset_dict, dataset_ref):

        ultima_atualizacao = self._object_value(dataset_ref, DCT.modified)

        if ultima_atualizacao:

            dataset_dict['ultima_atualizacao'] = parse(ultima_atualizacao, dayfirst=True).date().strftime('%d/%m/%Y')

        for _, _, o1 in self.g.triples((dataset_ref, DCT.temporal, None)):

            for _, _, o2 in self.g.triples((o1, DCAT.endDate, None)):

                dataset_dict['data_fim'] = o2
        
        qtd = self._object_value(dataset_ref, VCARD.Individual)
        vcard = False
        tipo = None

        if qtd:

            dataset_dict['quantidade'] = 'Indivíduo'
            tipo = VCARD.Individual
            vcard = True

        elif self._object_value(dataset_ref, VCARD.Group):

            dataset_dict['quantidade'] = 'Coletivo'
            tipo = VCARD.Group
            vcard = True

        if vcard:

            for _, _, o1 in self.g.triples((dataset_ref, tipo, None)):

                cidade = self._object_value(o1, VCARD.locality)

                if cidade:

                    dataset_dict['cidade'] = cidade

                estado = self._object_value(o1, VCARD.region)

                if estado:

                    dataset_dict['estado'] = estado

                for _, _, o2 in self.g.triples((o1, VCARD.hasAddress, None)):

                    cidades_atuacao = self._object_value(o2, VCARD.locality)

                    dataset_dict['cidade_atuacao'] = [cidade.strip() for cidade in cidades_atuacao.split(';')]

                    estados_atuacao = self._object_value(o2, VCARD.region)

                    dataset_dict['estado_atuacao'] = [estado.strip() for estado in estados_atuacao.split(';')]

                    paises_atuacao = self._object_value(o2, VCARD['country-name'])

                    dataset_dict['pais_atuacao'] = [pais.strip() for pais in paises_atuacao.split(';')]

                data_inicio = self._object_value(o1, VCARD.bday)

                if data_inicio:

                    dataset_dict['data_inicio'] = data_inicio
                
                for _, _, o2 in self.g.triples((o1, VCARD.hasGender, None)):

                    genero = self._object_value(o2, VCARD.value)

                    dataset_dict['genero'] = genero

                linguagem = self._object_value(o1, VCARD.category)

                if linguagem:

                    dataset_dict['linguagens'] = [linguagem]

                else:

                    for _, _, o2 in self.g.triples((o1, VCARD.hasCategory, None)):

                        linguagens = self._object_value_list(o2, VCARD.value)

                        dataset_dict['linguagens'] = [linguagem for linguagem in linguagens]

                url = self._object_value(o1, VCARD.url)

                if url:

                    dataset_dict['links'] = [url]

                else:

                    for _, _, o2 in self.g.triples((o1, VCARD.hasURL, None)):

                        urls = self._object_value_list(o2, VCARD.value)

                        dataset_dict['links'] = [url for url in urls]

        for distribution in self._distributions(dataset_ref):
            distribution_ref = str(distribution)
            for resource_dict in dataset_dict.get("resources", []):
                # Match distribution in graph and distribution in resource dict
                if resource_dict and distribution_ref == resource_dict.get(
                    "distribution_ref"
                ):
                    
                    for _, _, o1 in self.g.triples((distribution, GSP.SpatialObject, None)):

                        for _, _, o2 in self.g.triples((o1, RDF.type, None)):

                            if o2 == GSP.hasArea:
                                resource_dict['area'] = self._object_value(o1, QUDT.value)

                            else:

                                resource_dict['comprimento'] = self._object_value(o1, QUDT.value)

                        for _, _, o2 in self.g.triples((o1, GSP.hasMetricLength, None)):

                           resource_dict['comprimento'] = float(o2)

                    data_criacao = self._object_value(distribution, DCT.issued)

                    resource_dict['data_criacao'] = parse(data_criacao, dayfirst=True).date().strftime('%d/%m/%Y')

                    fonte = self._object_value(distribution, FOAF.page)

                    if fonte:

                        resource_dict['fonte'] = fonte

                    for _, _, o1 in self.g.triples((distribution, VRA.work, None)):

                        for _, _, o2 in self.g.triples((o1, RDF.type, None)):

                            resource_dict['tecnica'] = self._object_value(o1, VRA.display)
                        
    def _graph_from_dataset_v3_presencas(self, dataset_dict, dataset_ref):

        g = self.g

        # Remove duplicata do contactPoint do scheming e v2

        for s1, p1, o1 in g.triples( (dataset_ref, DCAT.contactPoint, None) ):

            for s2, p2, o2 in g.triples( (o1, RDF.type, VCARD.Kind) ):

                g.remove( (s2, VCARD.fn, None) )
                g.remove( (s2, VCARD.hasEmail, None) )
                g.remove( (s2, VCARD.hasUID, None) )

                g.remove( (s2, p2, o2) )
                g.remove( (s1, p1, o1) )

        ind_grupo_coletivo = self._get_dataset_value(dataset_dict, 'quantidade')

        if ind_grupo_coletivo != None:

            ind_grupo_coletivo = ind_grupo_coletivo if ind_grupo_coletivo != "" else "individuo"

            ind_grupo_coletivo_no = BNode()
            adicionou = False

            if ind_grupo_coletivo.lower() == "indivíduo" or ind_grupo_coletivo.lower() == "individuo":

                g.add( (dataset_ref, VCARD.Individual, ind_grupo_coletivo_no) )
                adicionou = True
            
            elif ind_grupo_coletivo.lower() == "coletivo" or ind_grupo_coletivo.lower() == "grupo":

                g.add( (dataset_ref, VCARD.Group, ind_grupo_coletivo_no) )
                adicionou = True

            if adicionou:

                g.add( ( ind_grupo_coletivo_no, VCARD.fn, Literal(self._get_dataset_value(dataset_dict, 'title')) ) )

            cidade = self._get_dataset_value(dataset_dict, 'cidade')

            if cidade:

                g.add( (ind_grupo_coletivo_no, VCARD.locality, Literal(cidade)) )

            estado = self._get_dataset_value(dataset_dict, 'estado')

            if estado:

                g.add( (ind_grupo_coletivo_no, VCARD.region, Literal(estado)) )

            cidades_atuacao = self._get_dataset_value(dataset_dict, 'cidade_atuacao')
            estados_atuacao = self._get_dataset_value(dataset_dict, 'estado_atuacao')
            paises_atuacao = self._get_dataset_value(dataset_dict, 'pais_atuacao')

            atuacao = None

            if cidades_atuacao or estados_atuacao or paises_atuacao:

                atuacao = BNode()

                g.add( (ind_grupo_coletivo_no, VCARD.hasAddress, atuacao) )

            if cidades_atuacao:

                if type(cidades_atuacao) != list:

                    cidades_atuacao = json.loads(json.dumps([cidades_atuacao]))

                cidades = ""

                for cidade_atuacao in cidades_atuacao:

                    cidades += cidade_atuacao + "; "

                g.add( (atuacao, VCARD.locality, Literal(cidades[:-2])) )

            if estados_atuacao: 

                if type(estados_atuacao) != list:

                    estados_atuacao = json.loads(json.dumps([estados_atuacao]))

                estados = ""

                for estado_atuacao in estados_atuacao:

                    estados += estado_atuacao + "; "

                g.add( (atuacao, VCARD.region, Literal(estados[:-2])) )


            if paises_atuacao:

                if type(paises_atuacao) != list:

                    paises_atuacao = json.loads(json.dumps([paises_atuacao]))

                paises = ""

                for pais_atuacao in paises_atuacao:

                    paises += pais_atuacao + "; "

                g.add( (atuacao, VCARD['country-name'], Literal(paises[:-2])) )


            data_inicio = self._get_dataset_value(dataset_dict, 'data_inicio')

            if data_inicio:

                if len(data_inicio) == 4:

                    g.add( (ind_grupo_coletivo_no, VCARD.bday, Literal(data_inicio, datatype=XSD.gYear)) )

                else:

                    g.add( (ind_grupo_coletivo_no, VCARD.bday, Literal(data_inicio, datatype=XSD.date)) )

            data_fim = self._get_dataset_value(dataset_dict, 'data_fim')

            if data_fim:

                for s, p, o in g.triples((None, DCT.temporal, None)):     # Remove o temporal_end do euro_dcat

                    for s2, p2, o2 in g.triples((o, None, None)):
                        g.remove((s2, p2, o2))
                    
                    g.remove((s, p, o))

                temporal = BNode()
                g.add( (temporal, RDF.type, DCT.PeriodOfTime) )
                self._add_date_triple(temporal, DCAT.endDate, data_fim)
                g.add((dataset_ref, DCT.temporal, temporal))

            genero = self._get_dataset_value(dataset_dict, 'genero')

            if genero:

                genero = genero.lower()

                genero_no = BNode()

                g.add( (ind_grupo_coletivo_no, VCARD.hasGender, genero_no) )
                g.add( (genero_no, VCARD.value, Literal(genero)) )

                if genero.startswith('cisfem') or genero.startswith('transfem'):

                    g.add( (genero_no, RDFS.Datatype, URIRefOrLiteral('http://www.w3.org/2006/vcard/ns#Female')) )

                elif genero.startswith('cismasc') or genero.startswith('transmasc'):

                    g.add( (genero_no, RDFS.Datatype, URIRefOrLiteral('http://www.w3.org/2006/vcard/ns#Male')) )

                else:

                    g.add( (genero_no, RDFS.Datatype, URIRefOrLiteral('http://www.w3.org/2006/vcard/ns#Other')) )

            linguagens = self._get_dataset_value(dataset_dict, 'linguagens')

            if linguagens:

                if type(linguagens) != list:

                    g.add ( (ind_grupo_coletivo_no, VCARD.category, Literal(linguagens)) )

                else:

                    linguagens_no = BNode()

                    g.add ( (ind_grupo_coletivo_no, VCARD.hasCategory, linguagens_no) )

                    for linguagem in linguagens:

                        g.add( (linguagens_no, VCARD.value, Literal(linguagem)) )

            ultima_atualizacao = self._get_dataset_value(dataset_dict, 'modified')

            if ultima_atualizacao:

                self._add_date_triple(dataset_ref, DCT.modified, ultima_atualizacao)

            links = self._get_dataset_value(dataset_dict, 'links')

            if links:

                if type(links) != list:

                    g.add ( (ind_grupo_coletivo_no, VCARD.url, URIRefOrLiteral(links)) )

                else:

                    links_no = BNode()

                    g.add ( (ind_grupo_coletivo_no, VCARD.hasURL, links_no) )

                    for link in links:

                        g.add( (links_no, VCARD.value, URIRefOrLiteral(link)) )
                        g.add ( (links_no, RDFS.Datatype, URIRefOrLiteral('http://www.w3.org/2006/vcard/ns#url')) )

        for resource_dict in dataset_dict.get("resources", []):

            distribution_ref = CleanedURIRef(resource_uri(resource_dict))

            fonte = self._get_resource_value(resource_dict, 'fonte')

            if fonte:

                g.add( (distribution_ref, FOAF.page, URIRefOrLiteral(fonte)) )

            if resource_dict.get('comprimento') or resource_dict.get('area'):

                objeto = BNode()

                if resource_dict.get('comprimento'):

                    try:

                        g.add( (objeto, GSP.hasMetricLength, Literal(float(resource_dict.get('comprimento')), datatype=XSD.double)) )

                    except (ValueError, TypeError):

                        g.add( (objeto, RDF.type, GSP.hasLength) )
                        g.add ( (objeto, QUDT.value, Literal(resource_dict.get('comprimento'))) )
                
                elif resource_dict.get('area'):

                    g.add( (objeto, RDF.type, GSP.hasArea) )

                    g.add( (objeto, QUDT.value, Literal(resource_dict.get('area'))) )

                g.add( (distribution_ref, GSP.SpatialObject, objeto) )

            data_criacao = self._get_resource_value(resource_dict, 'data_criacao')

            if data_criacao:

                for s, p, o in g.triples((distribution_ref, DCT.issued, None)):     # Remove o issued do euro_dcat

                    g.remove((s, p, o))

                self._add_date_triple(distribution_ref, DCT.issued, data_criacao)

            tecnica = self._get_resource_value(resource_dict, 'tecnica')

            if tecnica:
               
                objeto = BNode()

                g.add( (objeto, RDF.type, VRA.techniqueSet) )

                g.add( (objeto, VRA.display, Literal(resource_dict.get('tecnica'))) )

                g.add( (distribution_ref, VRA.work, objeto) )