import random

def random_13_digits():
    # Generate a random 13-digit number
    return random.randint(1000000000000, 9999999999999)

def get_human_payload(positive_prompt, width=768, height=1024):
    """Return the payload for prompts containing human-related keywords."""
    return {
        "client_id": "ec613a70350945ab9d33de76d7bc298e",
        "prompt": {
            "3": {
                "inputs": {
                    "seed": random_13_digits(),
                    "steps": 60,
                    "cfg": 7,
                    "sampler_name": "dpmpp_sde",
                    "scheduler": "karras",
                    "denoise": 1,
                    "model": ["10", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "4": {
                "inputs": {
                    "ckpt_name": "realisticVisionV60B1_v51VAE.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"}
            },
            "6": {
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["10", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "7": {
                "inputs": {
                    "text": "low-res, bad anatomy, incorrect anatomy, deformed limbs, extra limbs, missing limbs, malformed hands, malformed feet, extra fingers, extra toes, fewer fingers, fewer toes, floating limbs, disconnected limbs, poorly drawn hands, poorly drawn feet, distorted proportions, unnatural poses, blurry, low quality, jpeg artifacts, watermark, text, signature, username, artist name, cropped, disfigured, mutated, unnatural",
                    "clip": ["10", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "9": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            },
            "10": {
                "inputs": {
                    "lora_name": "Hands.safetensors",
                    "strength_model": 0.8500000000000002,
                    "strength_clip": 0.8500000000000002,
                    "model": ["17", 0],
                    "clip": ["17", 1]
                },
                "class_type": "LoraLoader",
                "_meta": {"title": "Load LoRA"}
            },
            "13": {
                "inputs": {
                    "lora_name": "Detail-Slider.safetensors",
                    "strength_model": 0.8000000000000002,
                    "strength_clip": 0.8000000000000002,
                    "model": ["4", 0],
                    "clip": ["4", 1]
                },
                "class_type": "LoraLoader",
                "_meta": {"title": "Load LoRA"}
            },
            "16": {
                "inputs": {
                    "lora_name": "better_body.safetensors",
                    "strength_model": 0.5000000000000001,
                    "strength_clip": 0.5000000000000001,
                    "model": ["13", 0],
                    "clip": ["13", 1]
                },
                "class_type": "LoraLoader",
                "_meta": {"title": "Load LoRA"}
            },
            "17": {
                "inputs": {
                    "lora_name": "mix4.safetensors",
                    "strength_model": 0.8000000000000002,
                    "strength_clip": 0.8000000000000002,
                    "model": ["16", 0],
                    "clip": ["16", 1]
                },
                "class_type": "LoraLoader",
                "_meta": {"title": "Load LoRA"}
            }
        },
        "extra_data": {
            "auth_token_comfy_org": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImE0YTEwZGVjZTk4MzY2ZDZmNjNlMTY3Mjg2YWU5YjYxMWQyYmFhMjciLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiVHJ1bmcgVsawxqFuZyIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKSHRhVzhnNjNmV0p1MUdyZ1VmQW1Kc2h1ZWJNcC11S205S0JmWDF0SXV4R0lHdGFjVD1zOTYtYyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9kcmVhbWJvb3RoeSIsImF1ZCI6ImRyZWFtYm9vdGh5IiwiYXV0aF90aW1lIjoxNzQ5NjcwNzc1LCJ1c2VyX2lkIjoiT1NuU3B6QjBwamh5R0JwaDlSaE9jeG9qVzBCMiIsInN1YiI6Ik9TblNwekIwcGpoeUdCcGg5UmhPY3hvalcwQjIiLCJpYXQiOjE3NDk5MDQ5NDQsImV4cCI6MTc0OTkwODU0NCwiZW1haWwiOiJ0cnVuZ3Z1b25nNTI4QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7Imdvb2dsZS5jb20iOlsiMTExNTg1NjAwOTA4MTkyMzk1MTMxIl0sImVtYWlsIjpbInRydW5ndnVvbmc1MjhAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.RG74eesUlm4fgJzyZ097NJHBV96dWhOcIfypfO1aQ_qJ5hhdlqShJPANjGIcteA50jRlrIbcdLt7WSwlh0__yTK6uvRwXzpERcm3uTGzoBubSABX6IhFkUSa7Du96ORpk_bpPETm4_TCLhROe43mlw-6L92P9TRhJWY-ByEB4HogmgyHxSYtkfi7QcmOFD7epTmxvoA_SHcfEzOcGOGsg7_tvCPOjMSTBb4t6bRbJJ86C_z_N4XOFF9F3_GjlpJAeZjxoqp4kEk6Dc39rLfvsY-0RMHbSerUuD9m2i7b6Eo6BsSitE6WhgQQluUrBgH7BYPGnBG4GNs54l-Wf287xg",
            "extra_pnginfo": {
                "workflow": {
                    "id": "ec95f019-3b14-4695-b3d0-14f263ec8a4d",
                    "revision": 0,
                    "last_node_id": 17,
                    "last_link_id": 62,
                    "nodes": [
                        {
                            "id": 8,
                            "type": "VAEDecode",
                            "pos": [1209, 188],
                            "size": [210, 46],
                            "flags": {},
                            "order": 9,
                            "mode": 0,
                            "inputs": [{"name": "samples", "type": "LATENT", "link": 7}, {"name": "vae", "type": "VAE", "link": 8}],
                            "outputs": [{"name": "IMAGE", "type": "IMAGE", "slot_index": 0, "links": [9]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "VAEDecode"},
                            "widgets_values": []
                        },
                        {
                            "id": 5,
                            "type": "EmptyLatentImage",
                            "pos": [486.7566833496094, 619.8082885742188],
                            "size": [315, 106],
                            "flags": {},
                            "order": 0,
                            "mode": 0,
                            "inputs": [],
                            "outputs": [{"name": "LATENT", "type": "LATENT", "slot_index": 0, "links": [2]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "EmptyLatentImage"},
                            "widgets_values": [768, 1024, 1]
                        },
                        {
                            "id": 4,
                            "type": "CheckpointLoaderSimple",
                            "pos": [-436.0419921875, 289.5413818359375],
                            "size": [315, 98],
                            "flags": {},
                            "order": 1,
                            "mode": 0,
                            "inputs": [],
                            "outputs": [
                                {"name": "MODEL", "type": "MODEL", "slot_index": 0, "links": [53]},
                                {"name": "CLIP", "type": "CLIP", "slot_index": 1, "links": [54]},
                                {"name": "VAE", "type": "VAE", "slot_index": 2, "links": [8]}
                            ],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "CheckpointLoaderSimple"},
                            "widgets_values": ["realisticVisionV60B1_v51VAE.safetensors"]
                        },
                        {
                            "id": 9,
                            "type": "SaveImage",
                            "pos": [1460.09814453125, 231.45758056640625],
                            "size": [497.4477233886719, 484.6128234863281],
                            "flags": {},
                            "order": 10,
                            "mode": 0,
                            "inputs": [{"name": "images", "type": "IMAGE", "link": 9}],
                            "outputs": [],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40"},
                            "widgets_values": ["ComfyUI"]
                        },
                        {
                            "id": 13,
                            "type": "LoraLoader",
                            "pos": [-22.86707305908203, 934.4988403320312],
                            "size": [270, 126],
                            "flags": {},
                            "order": 2,
                            "mode": 0,
                            "inputs": [{"name": "model", "type": "MODEL", "link": 53}, {"name": "clip", "type": "CLIP", "link": 54}],
                            "outputs": [
                                {"name": "MODEL", "type": "MODEL", "links": [55]},
                                {"name": "CLIP", "type": "CLIP", "links": [56]}
                            ],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "LoraLoader"},
                            "widgets_values": ["Detail-Slider.safetensors", 0.8000000000000002, 0.8000000000000002]
                        },
                        {
                            "id": 10,
                            "type": "LoraLoader",
                            "pos": [-19.905139923095703, 289.1090087890625],
                            "size": [270, 126],
                            "flags": {},
                            "order": 5,
                            "mode": 0,
                            "inputs": [{"name": "model", "type": "MODEL", "link": 61}, {"name": "clip", "type": "CLIP", "link": 62}],
                            "outputs": [
                                {"name": "MODEL", "type": "MODEL", "links": [40]},
                                {"name": "CLIP", "type": "CLIP", "links": [41, 42]}
                            ],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "LoraLoader"},
                            "widgets_values": ["Hands.safetensors", 0.8500000000000002, 0.8500000000000002]
                        },
                        {
                            "id": 17,
                            "type": "LoraLoader",
                            "pos": [-22.762775421142578, 501.7164001464844],
                            "size": [270, 126],
                            "flags": {},
                            "order": 4,
                            "mode": 0,
                            "inputs": [{"name": "model", "type": "MODEL", "link": 59}, {"name": "clip", "type": "CLIP", "link": 60}],
                            "outputs": [
                                {"name": "MODEL", "type": "MODEL", "links": [61]},
                                {"name": "CLIP", "type": "CLIP", "links": [62]}
                            ],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "LoraLoader"},
                            "widgets_values": ["mix4.safetensors", 0.8000000000000002, 0.8000000000000002]
                        },
                        {
                            "id": 16,
                            "type": "LoraLoader",
                            "pos": [-29.07598876953125, 707.1071166992188],
                            "size": [270, 126],
                            "flags": {},
                            "order": 3,
                            "mode": 0,
                            "inputs": [{"name": "model", "type": "MODEL", "link": 55}, {"name": "clip", "type": "CLIP", "link": 56}],
                            "outputs": [
                                {"name": "MODEL", "type": "MODEL", "links": [59]},
                                {"name": "CLIP", "type": "CLIP", "links": [60]}
                            ],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "LoraLoader"},
                            "widgets_values": ["better_body.safetensors", 0.5000000000000001, 0.5000000000000001]
                        },
                        {
                            "id": 3,
                            "type": "KSampler",
                            "pos": [867.2566528320312, 193.18141174316406],
                            "size": [315, 262],
                            "flags": {},
                            "order": 8,
                            "mode": 0,
                            "inputs": [
                                {"name": "model", "type": "MODEL", "link": 40},
                                {"name": "positive", "type": "CONDITIONING", "link": 4},
                                {"name": "negative", "type": "CONDITIONING", "link": 6},
                                {"name": "latent_image", "type": "LATENT", "link": 2}
                            ],
                            "outputs": [{"name": "LATENT", "type": "LATENT", "slot_index": 0, "links": [7]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "KSampler"},
                            "widgets_values": [random_13_digits(), "randomize", 60, 6.5, "dpmpp_sde", "karras", 1]
                        },
                        {
                            "id": 7,
                            "type": "CLIPTextEncode",
                            "pos": [413, 389],
                            "size": [425.27801513671875, 180.6060791015625],
                            "flags": {},
                            "order": 7,
                            "mode": 0,
                            "inputs": [{"name": "clip", "type": "CLIP", "link": 42}],
                            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [6]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "CLIPTextEncode"},
                            "widgets_values": [
                                "score_6_up, score_5_up, score_4_up, low-res, bad anatomy, incorrect anatomy, deformed limbs, extra limbs, missing limbs, malformed hands, malformed feet, extra fingers, extra toes, fewer fingers, fewer toes, floating limbs, disconnected limbs, poorly drawn hands, poorly drawn feet, distorted proportions, unnatural poses, blurry, low quality, jpeg artifacts, watermark, text, signature, username, artist name, cropped, disfigured, mutated, unnatural"
                            ]
                        },
                        {
                            "id": 6,
                            "type": "CLIPTextEncode",
                            "pos": [416.0834655761719, 174.08181762695312],
                            "size": [422.84503173828125, 164.31304931640625],
                            "flags": {},
                            "order": 6,
                            "mode": 0,
                            "inputs": [{"name": "clip", "type": "CLIP", "link": 41}],
                            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [4]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "CLIPTextEncode"},
                            "widgets_values": [positive_prompt]
                        }
                    ],
                    "links": [
                        [2, 5, 0, 3, 3, "LATENT"],
                        [4, 6, 0, 3, 1, "CONDITIONING"],
                        [6, 7, 0, 3, 2, "CONDITIONING"],
                        [7, 3, 0, 8, 0, "LATENT"],
                        [8, 4, 2, 8, 1, "VAE"],
                        [9, 8, 0, 9, 0, "IMAGE"],
                        [40, 10, 0, 3, 0, "MODEL"],
                        [41, 10, 1, 6, 0, "CLIP"],
                        [42, 10, 1, 7, 0, "CLIP"],
                        [53, 4, 0, 13, 0, "MODEL"],
                        [54, 4, 1, 13, 1, "CLIP"],
                        [55, 13, 0, 16, 0, "MODEL"],
                        [56, 13, 1, 16, 1, "CLIP"],
                        [59, 16, 0, 17, 0, "MODEL"],
                        [60, 16, 1, 17, 1, "CLIP"],
                        [61, 17, 0, 10, 0, "MODEL"],
                        [62, 17, 1, 10, 1, "CLIP"]
                    ],
                    "groups": [],
                    "config": {},
                    "extra": {
                        "ds": {
                            "scale": 0.5209868481924489,
                            "offset": [-18.485386598558176, 127.79789000727102]
                        },
                        "frontendVersion": "1.21.7"
                    },
                    "version": 0.4
                }
            }
        }
    }

def get_non_human_payload(positive_prompt, width=768, height=1024):
    """Return the payload for prompts not containing human-related keywords."""
    return {
        "client_id": "85ee56d4d96945c78809ef5af4b6458f",
        "prompt": {
            "3": {
                "inputs": {
                    "seed": random_13_digits(),
                    "steps": 40,
                    "cfg": 7,
                    "sampler_name": "dpmpp_sde",
                    "scheduler": "karras",
                    "denoise": 1,
                    "model": ["18", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "KSampler"}
            },
            "4": {
                "inputs": {
                    "ckpt_name": "realisticVisionV60B1_v51VAE.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {"title": "Load Checkpoint"}
            },
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {"title": "Empty Latent Image"}
            },
            "6": {
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["18", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "7": {
                "inputs": {
                    "text": "low-res, bad anatomy, incorrect anatomy, deformed limbs, extra limbs, missing limbs, malformed hands, malformed feet, extra fingers, extra toes, fewer fingers, fewer toes, floating limbs, disconnected limbs, poorly drawn hands, poorly drawn feet, distorted proportions, unnatural poses, blurry, low quality, jpeg artifacts, watermark, text, signature, username, artist name, cropped, disfigured, mutated, unnatural",
                    "clip": ["18", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode (Prompt)"}
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE Decode"}
            },
            "9": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"}
            },
            "18": {
                "inputs": {
                    "lora_name": "Detail-Slider.safetensors",
                    "strength_model": 0.8000000000000002,
                    "strength_clip": 0.8000000000000002,
                    "model": ["4", 0],
                    "clip": ["4", 1]
                },
                "class_type": "LoraLoader",
                "_meta": {"title": "Load LoRA"}
            }
        },
        "extra_data": {
            "auth_token_comfy_org": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImE0YTEwZGVjZTk4MzY2ZDZmNjNlMTY3Mjg2YWU5YjYxMWQyYmFhMjciLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiVHJ1bmcgVsawxqFuZyIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NKSHRhVzhnNjNmV0p1MUdyZ1VmQW1Kc2h1ZWJNcC11S205S0JmWDF0SXV4R0lHdGFjVD1zOTYtYyIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9kcmVhbWJvb3RoeSIsImF1ZCI6ImRyZWFtYm9vdGh5IiwiYXV0aF90aW1lIjoxNzQ5NjcwNzc1LCJ1c2VyX2lkIjoiT1NuU3B6QjBwamh5R0JwaDlSaE9jeG9qVzBCMiIsInN1YiI6Ik9TblNwekIwcGpoeUdCcGg5UmhPY3hvalcwQjIiLCJpYXQiOjE3NDk5MTA2NTYsImV4cCI6MTc0OTkxNDI1NiwiZW1haWwiOiJ0cnVuZ3Z1b25nNTI4QGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7Imdvb2dsZS5jb20iOlsiMTExNTg1NjAwOTA4MTkyMzk1MTMxIl0sImVtYWlsIjpbInRydW5ndnVvbmc1MjhAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.dBybGciISTWHWzeaCSJgagBTAIeEeGp0HS0kmC1E129lsMk3SLavKhU7WcDFAw0nV1STalxkml2upDj1bH01OmOx1Iy6BAnqlrwcL-Fh66JU_l87GmoAeXEF2VX0oUfL7G3w6pIuqaVpTys6t2nMrWu9Jm8IWvJ5k5d2QcTmvAIAje3A5CK84RGSs8jwGiZ9K7jCwH1JohpLbSZUm-XwpH0S_a87qo9gx3GDJ4eYBE17GnHmnHewS4nRl0ERZZ1FpyphbMAAY9XVnQjq7YBF2Dt1PEIm_qTGpdU_tUToZtODL5DUEXIgtcWRbdY8u7dW2KHRNZKCbJ5ENzenJvNsbg",
            "extra_pnginfo": {
                "workflow": {
                    "id": "ec95f019-3b14-4695-b3d0-14f263ec8a4d",
                    "revision": 0,
                    "last_node_id": 18,
                    "last_link_id": 78,
                    "nodes": [
                        {
                            "id": 5,
                            "type": "EmptyLatentImage",
                            "pos": [486.7566833496094, 619.8082885742188],
                            "size": [315, 106],
                            "flags": {},
                            "order": 0,
                            "mode": 0,
                            "inputs": [],
                            "outputs": [{"name": "LATENT", "type": "LATENT", "slot_index": 0, "links": [2]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "EmptyLatentImage"},
                            "widgets_values": [768, 1024, 1]
                        },
                        {
                            "id": 4,
                            "type": "CheckpointLoaderSimple",
                            "pos": [-436.0419921875, 289.5413818359375],
                            "size": [315, 98],
                            "flags": {},
                            "order": 1,
                            "mode": 0,
                            "inputs": [],
                            "outputs": [
                                {"name": "MODEL", "type": "MODEL", "slot_index": 0, "links": [77]},
                                {"name": "CLIP", "type": "CLIP", "slot_index": 1, "links": [74]},
                                {"name": "VAE", "type": "VAE", "slot_index": 2, "links": [8]}
                            ],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "CheckpointLoaderSimple"},
                            "widgets_values": ["realisticVisionV60B1_v51VAE.safetensors"]
                        },
                        {
                            "id": 9,
                            "type": "SaveImage",
                            "pos": [1460.09814453125, 231.45758056640625],
                            "size": [497.4477233886719, 484.6128234863281],
                            "flags": {},
                            "order": 7,
                            "mode": 0,
                            "inputs": [{"name": "images", "type": "IMAGE", "link": 9}],
                            "outputs": [],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40"},
                            "widgets_values": ["ComfyUI"]
                        },
                        {
                            "id": 7,
                            "type": "CLIPTextEncode",
                            "pos": [413, 389],
                            "size": [425.27801513671875, 180.6060791015625],
                            "flags": {},
                            "order": 3,
                            "mode": 0,
                            "inputs": [{"name": "clip", "type": "CLIP", "link": 75}],
                            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [6]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "CLIPTextEncode"},
                            "widgets_values": [
                                "low-res, bad anatomy, incorrect anatomy, deformed limbs, extra limbs, missing limbs, malformed hands, malformed feet, extra fingers, extra toes, fewer fingers, fewer toes, floating limbs, disconnected limbs, poorly drawn hands, poorly drawn feet, distorted proportions, unnatural poses, blurry, low quality, jpeg artifacts, watermark, text, signature, username, artist name, cropped, disfigured, mutated, unnatural"
                            ]
                        },
                        {
                            "id": 8,
                            "type": "VAEDecode",
                            "pos": [1237.8924560546875, 175.3594970703125],
                            "size": [210, 46],
                            "flags": {},
                            "order": 6,
                            "mode": 0,
                            "inputs": [{"name": "samples", "type": "LATENT", "link": 7}, {"name": "vae", "type": "VAE", "link": 8}],
                            "outputs": [{"name": "IMAGE", "type": "IMAGE", "slot_index": 0, "links": [9]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "VAEDecode"},
                            "widgets_values": []
                        },
                        {
                            "id": 3,
                            "type": "KSampler",
                            "pos": [884.729248046875, 176.89772033691406],
                            "size": [315, 262],
                            "flags": {},
                            "order": 5,
                            "mode": 0,
                            "inputs": [
                                {"name": "model", "type": "MODEL", "link": 78},
                                {"name": "positive", "type": "CONDITIONING", "link": 4},
                                {"name": "negative", "type": "CONDITIONING", "link": 6},
                                {"name": "latent_image", "type": "LATENT", "link": 2}
                            ],
                            "outputs": [{"name": "LATENT", "type": "LATENT", "slot_index": 0, "links": [7]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "KSampler"},
                            "widgets_values": [random_13_digits(), "randomize", 60, 7, "dpmpp_sde", "karras", 1]
                        },
                        {
                            "id": 18,
                            "type": "LoraLoader",
                            "pos": [10.653985977172852, 291.4464416503906],
                            "size": [270, 126],
                            "flags": {},
                            "order": 2,
                            "mode": 0,
                            "inputs": [{"name": "model", "type": "MODEL", "link": 77}, {"name": "clip", "type": "CLIP", "link": 74}],
                            "outputs": [
                                {"name": "MODEL", "type": "MODEL", "links": [78]},
                                {"name": "CLIP", "type": "CLIP", "links": [75, 76]}
                            ],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "LoraLoader"},
                            "widgets_values": ["Detail-Slider.safetensors", 1, 1]
                        },
                        {
                            "id": 6,
                            "type": "CLIPTextEncode",
                            "pos": [416.0834655761719, 174.08181762695312],
                            "size": [422.84503173828125, 164.31304931640625],
                            "flags": {},
                            "order": 4,
                            "mode": 0,
                            "inputs": [{"name": "clip", "type": "CLIP", "link": 76}],
                            "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": [4]}],
                            "properties": {"cnr_id": "comfy-core", "ver": "0.3.40", "Node name for S&R": "CLIPTextEncode"},
                            "widgets_values": [positive_prompt]
                        }
                    ],
                    "links": [
                        [2, 5, 0, 3, 3, "LATENT"],
                        [4, 6, 0, 3, 1, "CONDITIONING"],
                        [6, 7, 0, 3, 2, "CONDITIONING"],
                        [7, 3, 0, 8, 0, "LATENT"],
                        [8, 4, 2, 8, 1, "VAE"],
                        [9, 8, 0, 9, 0, "IMAGE"],
                        [74, 4, 1, 18, 1, "CLIP"],
                        [75, 18, 1, 7, 0, "CLIP"],
                        [76, 18, 1, 6, 0, "CLIP"],
                        [77, 4, 0, 18, 0, "MODEL"],
                        [78, 18, 0, 3, 0, "MODEL"]
                    ],
                    "groups": [],
                    "config": {},
                    "extra": {
                        "ds": {
                            "scale": 0.7627768444385666,
                            "offset": [-82.55866058849041, 71.71194837651413]
                        },
                        "frontendVersion": "1.21.7"
                    },
                    "version": 0.4
                }
            }
        }
    }
