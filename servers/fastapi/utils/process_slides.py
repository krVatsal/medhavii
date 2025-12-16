import asyncio
from typing import List, Tuple, Union
from models.image_prompt import ImagePrompt
from models.sql.image_asset import ImageAsset
from models.sql.video_asset import VideoAsset
from models.sql.slide import SlideModel
from services.icon_finder_service import ICON_FINDER_SERVICE
from services.image_generation_service import ImageGenerationService
from services.manim_service import MANIM_SERVICE
from utils.asset_directory_utils import get_images_directory
from utils.dict_utils import get_dict_at_path, get_dict_paths_with_key, set_dict_at_path
from utils.get_env import get_app_data_directory_env
import os


async def process_slide_and_fetch_assets(
    image_generation_service: ImageGenerationService,
    slide: SlideModel,
) -> List[Union[ImageAsset, VideoAsset]]:

    async_tasks = []

    image_paths = get_dict_paths_with_key(slide.content, "__image_prompt__")
    icon_paths = get_dict_paths_with_key(slide.content, "__icon_query__")
    video_paths = get_dict_paths_with_key(slide.content, "__video_prompt__")

    for image_path in image_paths:
        __image_prompt__parent = get_dict_at_path(slide.content, image_path)
        async_tasks.append(
            image_generation_service.generate_image(
                ImagePrompt(
                    prompt=__image_prompt__parent["__image_prompt__"],
                )
            )
        )

    for icon_path in icon_paths:
        __icon_query__parent = get_dict_at_path(slide.content, icon_path)
        async_tasks.append(
            ICON_FINDER_SERVICE.search_icons(__icon_query__parent["__icon_query__"])
        )
    
    for video_path in video_paths:
        __video_prompt__parent = get_dict_at_path(slide.content, video_path)
        async_tasks.append(
            MANIM_SERVICE.generate_video(__video_prompt__parent["__video_prompt__"])
        )

    results = await asyncio.gather(*async_tasks)
    results.reverse()

    app_data_dir = get_app_data_directory_env()

    return_assets = []
    for image_path in image_paths:
        image_dict = get_dict_at_path(slide.content, image_path)
        result = results.pop()
        if isinstance(result, ImageAsset):
            return_assets.append(result)
            if result.path.startswith(app_data_dir):
                relative_path = os.path.relpath(result.path, app_data_dir)
                relative_path = relative_path.replace(os.sep, "/")
                image_dict["__image_url__"] = f"/app_data/{relative_path}"
            else:
                image_dict["__image_url__"] = result.path
        else:
            image_dict["__image_url__"] = result
        set_dict_at_path(slide.content, image_path, image_dict)

    for icon_path in icon_paths:
        icon_dict = get_dict_at_path(slide.content, icon_path)
        icon_dict["__icon_url__"] = results.pop()[0]
        set_dict_at_path(slide.content, icon_path, icon_dict)
    
    for video_path in video_paths:
        video_dict = get_dict_at_path(slide.content, video_path)
        result = results.pop()
        if isinstance(result, VideoAsset):
            return_assets.append(result)
            if result.path.startswith(app_data_dir):
                relative_path = os.path.relpath(result.path, app_data_dir)
                relative_path = relative_path.replace(os.sep, "/")
                video_dict["__video_url__"] = f"/app_data/{relative_path}"
            else:
                video_dict["__video_url__"] = result.path
        else:
            # Handle failure or None
            video_dict["__video_url__"] = None
        set_dict_at_path(slide.content, video_path, video_dict)

    return return_assets


async def process_old_and_new_slides_and_fetch_assets(
    image_generation_service: ImageGenerationService,
    old_slide_content: dict,
    new_slide_content: dict,
) -> List[Union[ImageAsset, VideoAsset]]:
    # Finds all old images
    old_image_dict_paths = get_dict_paths_with_key(
        old_slide_content, "__image_prompt__"
    )
    old_image_dicts = [
        get_dict_at_path(old_slide_content, path) for path in old_image_dict_paths
    ]
    old_image_prompts = [
        old_image_dict["__image_prompt__"] for old_image_dict in old_image_dicts
    ]

    # Finds all old icons
    old_icon_dict_paths = get_dict_paths_with_key(old_slide_content, "__icon_query__")
    old_icon_dicts = [
        get_dict_at_path(old_slide_content, path) for path in old_icon_dict_paths
    ]
    old_icon_queries = [
        old_icon_dict["__icon_query__"] for old_icon_dict in old_icon_dicts
    ]

    # Finds all old videos
    old_video_dict_paths = get_dict_paths_with_key(old_slide_content, "__video_prompt__")
    old_video_dicts = [
        get_dict_at_path(old_slide_content, path) for path in old_video_dict_paths
    ]
    old_video_prompts = [
        old_video_dict["__video_prompt__"] for old_video_dict in old_video_dicts
    ]

    # Finds all new images
    new_image_dict_paths = get_dict_paths_with_key(
        new_slide_content, "__image_prompt__"
    )
    new_image_dicts = [
        get_dict_at_path(new_slide_content, path) for path in new_image_dict_paths
    ]

    # Finds all new icons
    new_icon_dict_paths = get_dict_paths_with_key(new_slide_content, "__icon_query__")
    new_icon_dicts = [
        get_dict_at_path(new_slide_content, path) for path in new_icon_dict_paths
    ]

    # Finds all new videos
    new_video_dict_paths = get_dict_paths_with_key(new_slide_content, "__video_prompt__")
    new_video_dicts = [
        get_dict_at_path(new_slide_content, path) for path in new_video_dict_paths
    ]

    # Creates async tasks for fetching new images
    async_image_fetch_tasks = []
    new_images_fetch_status = []

    # Creates async tasks for fetching new icons
    async_icon_fetch_tasks = []
    new_icons_fetch_status = []

    # Creates async tasks for fetching new videos
    async_video_fetch_tasks = []
    new_videos_fetch_status = []

    # Creates async tasks for fetching new images
    # Use old image url if prompt is same
    for new_image in new_image_dicts:
        if new_image["__image_prompt__"] in old_image_prompts:
            old_image_url = old_image_dicts[
                old_image_prompts.index(new_image["__image_prompt__"])
            ]["__image_url__"]
            new_image["__image_url__"] = old_image_url
            new_images_fetch_status.append(False)
            continue

        async_image_fetch_tasks.append(
            image_generation_service.generate_image(
                ImagePrompt(
                    prompt=new_image["__image_prompt__"],
                )
            )
        )
        new_images_fetch_status.append(True)

    # Creates async tasks for fetching new icons
    # Use old icon url if query is same
    for new_icon in new_icon_dicts:
        if new_icon["__icon_query__"] in old_icon_queries:
            old_icon_url = old_icon_dicts[
                old_icon_queries.index(new_icon["__icon_query__"])
            ]["__icon_url__"]
            new_icon["__icon_url__"] = old_icon_url
            new_icons_fetch_status.append(False)
            continue

        async_icon_fetch_tasks.append(
            ICON_FINDER_SERVICE.search_icons(new_icon["__icon_query__"])
        )
        new_icons_fetch_status.append(True)

    # Creates async tasks for fetching new videos
    # Use old video url if prompt is same
    for new_video in new_video_dicts:
        if new_video["__video_prompt__"] in old_video_prompts:
            old_video_url = old_video_dicts[
                old_video_prompts.index(new_video["__video_prompt__"])
            ]["__video_url__"]
            new_video["__video_url__"] = old_video_url
            new_videos_fetch_status.append(False)
            continue

        async_video_fetch_tasks.append(
            MANIM_SERVICE.generate_video(new_video["__video_prompt__"])
        )
        new_videos_fetch_status.append(True)

    new_images = await asyncio.gather(*async_image_fetch_tasks)
    new_icons = await asyncio.gather(*async_icon_fetch_tasks)
    new_videos = await asyncio.gather(*async_video_fetch_tasks)

    app_data_dir = get_app_data_directory_env()

    # list of new assets
    new_assets = []

    # Sets new image and icon urls for assets that were fetched
    # We need to iterate through the original dicts and update them, but we only have results for the ones we fetched.
    # We can use the status list to know which ones were fetched.
    
    # Images
    fetched_image_index = 0
    for i, new_image in enumerate(new_image_dicts):
        if new_images_fetch_status[i]:
            fetched_image = new_images[fetched_image_index]
            fetched_image_index += 1
            if isinstance(fetched_image, ImageAsset):
                new_assets.append(fetched_image)
                if fetched_image.path.startswith(app_data_dir):
                    relative_path = os.path.relpath(fetched_image.path, app_data_dir)
                    relative_path = relative_path.replace(os.sep, "/")
                    image_url = f"/app_data/{relative_path}"
                else:
                    image_url = fetched_image.path
            else:
                image_url = fetched_image
            new_image["__image_url__"] = image_url
        set_dict_at_path(new_slide_content, new_image_dict_paths[i], new_image)

    # Icons
    fetched_icon_index = 0
    for i, new_icon in enumerate(new_icon_dicts):
        if new_icons_fetch_status[i]:
            fetched_icon_result = new_icons[fetched_icon_index]
            fetched_icon_index += 1
            new_icon["__icon_url__"] = fetched_icon_result[0]
        set_dict_at_path(new_slide_content, new_icon_dict_paths[i], new_icon)

    # Videos
    fetched_video_index = 0
    for i, new_video in enumerate(new_video_dicts):
        if new_videos_fetch_status[i]:
            fetched_video = new_videos[fetched_video_index]
            fetched_video_index += 1
            if isinstance(fetched_video, VideoAsset):
                new_assets.append(fetched_video)
                if fetched_video.path.startswith(app_data_dir):
                    relative_path = os.path.relpath(fetched_video.path, app_data_dir)
                    relative_path = relative_path.replace(os.sep, "/")
                    video_url = f"/app_data/{relative_path}"
                else:
                    video_url = fetched_video.path
            else:
                video_url = None
            new_video["__video_url__"] = video_url
        set_dict_at_path(new_slide_content, new_video_dict_paths[i], new_video)

    return new_assets

    return new_assets


def process_slide_add_placeholder_assets(slide: SlideModel):

    image_paths = get_dict_paths_with_key(slide.content, "__image_prompt__")
    icon_paths = get_dict_paths_with_key(slide.content, "__icon_query__")
    video_paths = get_dict_paths_with_key(slide.content, "__video_prompt__")

    for image_path in image_paths:
        image_dict = get_dict_at_path(slide.content, image_path)
        image_dict["__image_url__"] = "/static/images/placeholder.jpg"
        set_dict_at_path(slide.content, image_path, image_dict)

    for icon_path in icon_paths:
        icon_dict = get_dict_at_path(slide.content, icon_path)
        icon_dict["__icon_url__"] = "/static/icons/placeholder.svg"
        set_dict_at_path(slide.content, icon_path, icon_dict)

    for video_path in video_paths:
        video_dict = get_dict_at_path(slide.content, video_path)
        video_dict["__video_url__"] = "/static/images/placeholder.jpg"
        set_dict_at_path(slide.content, video_path, video_dict)
