import path from 'path';
import fs from 'fs-extra';
import _ from 'lodash';

import Response from '@/lib/response/Response.ts';
import question from "./question.ts";

export default [
    {
        get: {
            "/": async () => {
                return new Response("Redirect to index page", { redirect: "/index.html" });
            },
            "/(.*)": async request => {
                let _path = request.params[0];
                if (!_.isString(_path))
                    return new Response('not found', {
                        type: 'html',
                        statusCode: 404
                    });
                const ext = path.extname(_path).substring(1);
                const filePath = path.join("public/", _path);
                if (!await fs.pathExists(filePath) || !(await fs.stat(filePath)).isFile()) {
                    return new Response('not found', {
                        type: 'html',
                        statusCode: 404
                    });
                }
                const { size: fileSize } = await fs.promises.stat(filePath);
                const readStream = fs.createReadStream(filePath);
                return new Response(readStream, {
                    type: ext || "txt",
                    headers: {
                        "Cache-Control": "max-age=31536000"  //对页面资源缓存设置一年有效期
                    },
                    size: fileSize
                });
            }
        }
    },
    question
];