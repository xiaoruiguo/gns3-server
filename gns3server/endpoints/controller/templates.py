# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
API endpoints for templates.
"""

import hashlib
import json

from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import Union, List
from uuid import UUID

from gns3server.endpoints.schemas.common import ErrorMessage
from gns3server.endpoints import schemas
from gns3server.controller import Controller

router = APIRouter()

import logging
log = logging.getLogger(__name__)

#template_create_models = Union[schemas.VPCSTemplateCreate, schemas.CloudTemplateCreate, schemas.IOUTemplateCreate]
#template_update_models = Union[schemas.VPCSTemplateUpdate, schemas.CloudTemplateUpdate, schemas.IOUTemplateUpdate]
#template_response_models = Union[schemas.VPCSTemplate, schemas.CloudTemplate, schemas.IOUTemplate]


@router.post("/templates",
             status_code=status.HTTP_201_CREATED,
             response_model=schemas.Template)
def create_template(template_data: schemas.TemplateCreate):

    controller = Controller.instance()
    template = controller.template_manager.add_template(jsonable_encoder(template_data, exclude_unset=True))
    # Reset the symbol list
    controller.symbols.list()
    return template.__json__()


@router.get("/templates/{template_id}",
            summary="List of all nodes",
            response_model=schemas.Template,
            response_model_exclude_unset=True,
            responses={404: {"model": ErrorMessage, "description": "Could not find template"}})
def get_template(template_id: UUID, request: Request, response: Response):

    request_etag = request.headers.get("If-None-Match", "")
    controller = Controller.instance()
    template = controller.template_manager.get_template(str(template_id))
    data = json.dumps(template.__json__())
    template_etag = '"' + hashlib.md5(data.encode()).hexdigest() + '"'
    if template_etag == request_etag:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED)
    else:
        response.headers["ETag"] = template_etag
        return template.__json__()


@router.put("/templates/{template_id}",
            response_model=schemas.Template,
            response_model_exclude_unset=True,
            responses={404: {"model": ErrorMessage, "description": "Template not found"}})
def update_template(template_id: UUID, template_data: schemas.TemplateUpdate):

    controller = Controller.instance()
    template = controller.template_manager.get_template(str(template_id))
    template.update(**jsonable_encoder(template_data, exclude_unset=True))
    return template.__json__()


@router.delete("/templates/{template_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               responses={404: {"model": ErrorMessage, "description": "Could not find template"}})
def delete_template(template_id: UUID):

    controller = Controller.instance()
    controller.template_manager.delete_template(str(template_id))


@router.get("/templates",
            response_model=List[schemas.Template],
            response_description="List of templates",
            response_model_exclude_unset=True)
def list_templates():

    controller = Controller.instance()
    return [c.__json__() for c in controller.template_manager.templates.values()]


@router.post("/templates/{template_id}/duplicate",
             response_model=schemas.Template,
             status_code=status.HTTP_201_CREATED,
             responses={404: {"model": ErrorMessage, "description": "Could not find template"}})
async def duplicate_template(template_id: UUID):

    controller = Controller.instance()
    template = controller.template_manager.duplicate_template(str(template_id))
    return template.__json__()


@router.post("/projects/{project_id}/templates/{template_id}",
             response_model=schemas.Node,
             status_code=status.HTTP_201_CREATED,
             responses={404: {"model": ErrorMessage, "description": "Could not find project or template"}})
async def create_node_from_template(project_id: UUID, template_id: UUID, template_usage: schemas.TemplateUsage):

    controller = Controller.instance()
    project = controller.get_project(str(project_id))
    node = await project.add_node_from_template(str(template_id),
                                                x=template_usage.x,
                                                y=template_usage.y,
                                                compute_id=template_usage.compute_id)
    return node.__json__()