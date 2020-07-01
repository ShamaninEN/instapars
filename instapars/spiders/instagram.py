# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import HtmlResponse
import re
import json
from urllib.parse import urlencode
from copy import deepcopy
from scrapy.loader import ItemLoader
from instapars.items import InstaparsItem



class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://instagram.com/']
    inst_login = 'flatsstore@yandex.ru'
    inst_pwd = '#PWD_INSTAGRAM_BROWSER:10:1593495385:AYRQAGuGiRsGGb+6c4g59rIT5NpB5FVnWWrXH2bjnM47qnhIxlnmwgK8hntULis4OUnvK0nO2Wf8D1xy5RmJCkcT9N+dNXctKyNTZI8mnKp6ZJDGpSvuHbirp+S+8qRgUwjMyh9+RhpfLXQDVg+WjWLTIk6W'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'

    post_hash = 'eddbde960fed6bde675388aac39a3657'
    graphql_url = 'https://www.instagram.com/graphql/query/?'
    follower_hash = 'c76146de99bb02f6415203be841dd25a'
    follow_hash = 'd04b0a864b4b54837c0d870b0e77e076'

    def parse(self, response):
        csrf_token = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.login_url,
            method='POST',
            callback=self.user_parse,
            formdata={
                'username': self.inst_login,
                'enc_password': self.inst_pwd
            },
            headers={'X-CSRFToken': csrf_token}
        )

    def user_parse(self, response: HtmlResponse):
        j_body = json.loads(response.text)
        if j_body['authenticated']:
            parse_user_str = input("Введите имена через пробел: ")
            parse_user_list = parse_user_str.split()
            for parse_user in parse_user_list:
                yield response.follow(
                    f'/{parse_user}',
                    callback=self.user_data_parse,
                    cb_kwargs={
                        'username': parse_user
                    }
                )

    def user_data_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        variables = {
            'id': user_id,
            'first': 24,
            'include_reel': True,
            'fetch_mutual': True
        }
        url_post = f'{self.graphql_url}query_hash={self.follower_hash}&{urlencode(variables)}'
        yield response.follow(
            url_post,
            callback=self.follower_list_parse,
            cb_kwargs={
                'username': username,
                'user_id': user_id,
                'variables': deepcopy(variables)
            }

        )

    def follower_list_parse(self, response: HtmlResponse, username, user_id, variables):
        j_data = json.loads(response.text)

        page_info = j_data.get('data').get('user').get('edge_followed_by').get('page_info')

        if page_info['has_next_page']:
            variables['after'] = page_info['end_cursor']
            variables['fetch_mutual'] = False
            variables['first'] = 15
            url_post = f'{self.graphql_url}query_hash={self.follower_hash}&{urlencode(variables)}'
            yield response.follow(
                url_post,
                callback=self.follower_list_parse,
                cb_kwargs={
                    'username': username,
                    'user_id': user_id,
                    'variables': deepcopy(variables)
                }
            )
        else:
            variables['first'] = 24
            variables.pop('after')
            url_post = f'{self.graphql_url}query_hash={self.follow_hash}&{urlencode(variables)}'
            yield response.follow(
                url_post,
                callback=self.follow_list_parse,
                cb_kwargs={
                    'username': username,
                    'user_id': user_id,
                    'variables': deepcopy(variables)
                }

            )
        followers = j_data.get('data').get('user').get('edge_followed_by').get('edges')
        for follower in followers:
            loader = ItemLoader(item=InstaparsItem(), response=response)
            loader.add_value('user_pars', username)
            loader.add_value('user_pars_id', user_id)
            loader.add_value('full_name', follower['node']['full_name'])
            loader.add_value('id', follower['node']['id'])
            loader.add_value('username', follower['node']['username'])
            loader.add_value('profile_pic_url', follower['node']['profile_pic_url'])
            loader.add_value('type', 'follower')
            yield loader.load_item()

    def follow_list_parse(self, response: HtmlResponse, username, user_id, variables):
        j_data = json.loads(response.text)

        page_info = j_data.get('data').get('user').get('edge_follow').get('page_info')

        if page_info['has_next_page']:
            variables['after'] = page_info['end_cursor']
            variables['fetch_mutual'] = False
            variables['first'] = 15
            url_post = f'{self.graphql_url}query_hash={self.follow_hash}&{urlencode(variables)}'
            yield response.follow(
                url_post,
                callback=self.follow_list_parse,
                cb_kwargs={
                    'username': username,
                    'user_id': user_id,
                    'variables': deepcopy(variables)
                }
            )

        follows = j_data.get('data').get('user').get('edge_follow').get('edges')
        # одинаковое действие можно объеденить и вынести в одну функцию принимать 2 аргумента
        for follow in follows:
            loader = ItemLoader(item=InstaparsItem(), response=response)
            loader.add_value('user_pars', username)
            loader.add_value('user_pars_id', user_id)
            loader.add_value('full_name', follow['node']['full_name'])
            loader.add_value('id', follow['node']['id'])
            loader.add_value('username', follow['node']['username'])
            loader.add_value('profile_pic_url', follow['node']['profile_pic_url'])
            loader.add_value('type', 'follow')
            yield loader.load_item()

    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')





